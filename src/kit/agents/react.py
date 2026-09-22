"""Generic, loop-controlled LangGraph ReAct agent builder."""

from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from kit.agents.react_state import (
    ReActState,
)
from kit.agents.tool_executor_node import (
    create_tool_executor_node,
)
from kit.context.builder import (
    ContextBudgetExceededError,
    ContextBuilder,
)
from kit.context.models import (
    ContextBudget,
    ContextCategory,
    ContextItem,
)
from kit.llms.tracker import (
    UsageTracker,
)
from kit.loops.controller import (
    LoopController,
)
from kit.loops.models import (
    LoopBudget,
    LoopStatus,
    StopReason,
)
from kit.tools.retry import (
    RetryPolicy,
)


def build_react_agent(
    *,
    model: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str,
    default_budget: LoopBudget | None = None,
    retry_policy: RetryPolicy | None = None,
    model_name: str | None = None,
    usage_tracker: UsageTracker | None = None,
    context_budget: ContextBudget | None = None,
):
    """Build a compiled LangGraph ReAct agent equipped with deterministic loop guards.

    Execution topology:
        START -> AGENT -> (tool calls?) -> GUARD -> (allowed?) -> TOOLS -> AGENT ...
                       -> (final answer?) -> COMPLETE -> END

    Features:
    - Iteration, tool-call, repeated-action, token, cost, failure, and context limits.
    - Controlled tool execution with transient error retry and exception sanitization.
    - Usage and pricing tracking from model response metadata.
    - Deterministic context construction with priority-based degradation.
    """
    budget = default_budget or LoopBudget()

    resolved_model_name = (
        model_name
        or getattr(model, "model_name", None)
        or getattr(model, "model", None)
        or getattr(model, "_model_name", None)
        or "default_model"
    )

    tracker = usage_tracker or UsageTracker()

    model_with_tools = model.bind_tools(tools)

    tool_node = create_tool_executor_node(
        tools,
        default_budget=budget,
        retry_policy=retry_policy,
    )

    async def agent_node(state: ReActState):
        """Invoke the LLM reasoning cycle and record usage.

        Enforces iteration budgets and context constraints.
        """
        controller = LoopController(
            budget=state.get("loop_budget", budget),
            status=state.get("loop_status", LoopStatus()),
        )

        controller.start_iteration()

        if not controller.can_continue:
            return {"loop_status": controller.status}

        # Context selection and bounding
        if context_budget is not None:
            items: list[ContextItem] = [
                ContextItem(
                    content=system_prompt,
                    category=ContextCategory.SYSTEM,
                    priority=100,
                    required=True,
                )
            ]
            for i, msg in enumerate(state["messages"]):
                is_first_human = isinstance(msg, HumanMessage) and i == 0
                category = (
                    ContextCategory.CURRENT_REQUEST
                    if is_first_human
                    else (
                        ContextCategory.TOOL_RESULT
                        if isinstance(msg, ToolMessage)
                        else ContextCategory.CONVERSATION
                    )
                )
                items.append(
                    ContextItem(
                        content=str(msg.content),
                        category=category,
                        priority=100 if is_first_human else 50,
                        required=is_first_human,
                        source_id=getattr(msg, "id", None) or str(i),
                    )
                )

            builder = ContextBuilder(budget=context_budget)
            try:
                build_result = builder.build(items)
            except ContextBudgetExceededError:
                controller.stop(StopReason.CONTEXT_BUDGET)
                return {"loop_status": controller.status}

            selected_source_ids = {
                item.source_id
                for item in build_result.selected
                if item.source_id is not None
            }
            filtered_messages = [
                msg
                for i, msg in enumerate(state["messages"])
                if (getattr(msg, "id", None) or str(i)) in selected_source_ids
            ]
            messages = [
                SystemMessage(content=system_prompt),
                *filtered_messages,
            ]
        else:
            messages = [
                SystemMessage(content=system_prompt),
                *state["messages"],
            ]

        response = await model_with_tools.ainvoke(messages)

        # Token & cost usage accounting
        usage = tracker.track(
            model=resolved_model_name,
            message=response,
        )

        controller.record_usage(
            input_tokens=usage.tokens.input_tokens,
            output_tokens=usage.tokens.output_tokens,
            cost_usd=usage.estimated_cost_usd,
        )

        return {
            "messages": [response],
            "loop_status": controller.status,
        }

    async def guard_tool_calls(state: ReActState):
        """Inspect proposed tool calls and detect repeated actions before execution."""
        controller = LoopController(
            budget=state.get("loop_budget", budget),
            status=state.get("loop_status", LoopStatus()),
        )

        message = state["messages"][-1]

        if not isinstance(message, AIMessage):
            return {"loop_status": controller.status}

        for tool_call in message.tool_calls or []:
            controller.record_tool_call(
                name=tool_call["name"],
                arguments=tool_call.get("args", {}),
            )

            if not controller.can_continue:
                break

        return {"loop_status": controller.status}

    def route_after_agent(state: ReActState):
        """Route to guard_tools if tools were requested, or complete if finished."""
        status = state["loop_status"]

        if status.stopped:
            return END

        message = state["messages"][-1]

        if isinstance(message, AIMessage) and message.tool_calls:
            return "guard_tools"

        return "complete"

    def route_after_guard(state: ReActState):
        """Halt loop if repetition/tool budget exceeded, otherwise proceed to tools."""
        if state["loop_status"].stopped:
            return END

        return "tools"

    def route_after_tools(state: ReActState):
        """Halt loop if failure budget exceeded, otherwise loop back to agent."""
        if state["loop_status"].stopped:
            return END

        return "agent"

    async def complete_node(state: ReActState):
        """Mark status explicitly with COMPLETED stop reason."""
        controller = LoopController(
            budget=state.get("loop_budget", budget),
            status=state.get("loop_status", LoopStatus()),
        )

        controller.complete()

        return {"loop_status": controller.status}

    graph = StateGraph(ReActState)

    graph.add_node("agent", agent_node)
    graph.add_node("guard_tools", guard_tool_calls)
    graph.add_node("tools", tool_node)
    graph.add_node("complete", complete_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route_after_agent)
    graph.add_conditional_edges("guard_tools", route_after_guard)
    graph.add_conditional_edges("tools", route_after_tools)
    graph.add_edge("complete", END)

    return graph.compile()
