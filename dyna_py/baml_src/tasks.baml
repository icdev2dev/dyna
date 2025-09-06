enum ExecutionMode {
    Sequential
    Parallel
    @@dynamic
}


enum CompletionPolicy {
    AllSubtasks
    AnySubtask
    KOfN
    @@dynamic
}

class Port {
    name string
    type string @description(#"Builtin (e.g., 'String', 'Int', 'JSON') or a custom class name"#)
    required bool?
}

class Completion {
    policy CompletionPolicy       @description(#"AllSubtasks=AND; AnySubtask=OR; KOfN=quorum"#)
    k int?                        @description(#"Used only when policy=KOfN; 1..N of direct subtasks"#)
}


class Task {
    id string
    title string?
    description string?

    executionMode ExecutionMode   @description(#"How this task runs its direct subtasks"#)
    subtasks Task[]?               @description(#"Recursive; array order = execution order when Sequential"#)
    dependsOn string[]?           @description(#"Cross-task deps by id (can point anywhere in the graph)"#)

    inputPorts Port[]?
    outputPorts Port[]?

    completion Completion?        @description(#"Defaults to AllSubtasks if omitted"#)

    agentId string?               @description(#"Automation/agent/tool ID"#)

    guard string?                 @description(#"Boolean expression gating execution"#)
}

class DataEdge  { 
    fromTaskId string
    fromPort string
    toTaskId string
    toPort string
}

class TaskGraph {
    tasks Task[]                  @description(#"All tasks (can include multiple roots)"#)
    roots string[]?               @description(#"Optional; else infer as tasks with no inbound deps"#)
    edges DataEdge[]?             @description(#"Typed dataflow across tasks; also implies ordering. An edge also implies a dependency from fromTaskId to toTaskId"#)
}

function GenerateTaskGraph(in_arg: string) -> TaskGraph {
    client CustomGPT4oMini
    prompt #"
You are a task graph planner. Produce a valid TaskGraph for the given instruction.

# Rules:

Return only a TaskGraph object, no extra text.
tasks: every task must have a unique id. Use short, stable, kebab-case IDs derived from titles.
Use executionMode=Sequential when steps must happen in order; use Parallel when independent work can run concurrently.
Completion defaults to AllSubtasks if omitted. For KOfN, set a valid k (1..len(subtasks)); otherwise do not use KOfN.
Use dependsOn for cross-branch requirements. If you use DataEdge, it implies a dependency; do not also duplicate it in dependsOn.
Declare inputPorts/outputPorts only when you connect tasks with DataEdge; ensure port types match exactly.
Keep the graph concise. Prefer 3–8 tasks unless the instruction clearly requires more.
Avoid empty arrays by omitting fields when not needed (e.g., subtasks, inputPorts, outputPorts, edges).
Set agentId only if the instruction suggests an automation/tool.


# Output shape:

roots: include top-level task IDs (those with no inbound deps).
edges: optional; include only if modeling typed data flow.
Use these heuristics:

Words like “in parallel”, “simultaneously”, “while”, “at the same time” → Parallel subtasks.
Independent API calls or per-region/per-platform work → Parallel.
Reviews/approvals after production steps → Sequential.
# Now generate the TaskGraph.

        {{ctx.output_format}}
        ------ GIVEN instruction ------
        {{in_arg}}
        ------ END GIVEN  instruction ------
        
    "#
}

enum TaskType {
    NA @description(#"
        Not applicable
    "#)
    TRANSLATION @description(#"
        only the act of translating from one language into another.
    "#)
    LOCALIZATION @description(#"
        only the task of localzing content from one language into another
    "#)
}

class ConstrainedTask {
    id string
    title string?
    description string?
    taskType TaskType

    executionMode ExecutionMode   @description(#"How this task runs its direct subtasks"#)
    subtasks ConstrainedTask[]               @description(#"Recursive; array order = execution order when Sequential"#)
    dependsOn string[]?           @description(#"Cross-task deps by id (can point anywhere in the graph)"#)

    inputPorts Port[]?
    outputPorts Port[]?

    completion Completion?        @description(#"Defaults to AllSubtasks if omitted"#)

    agentId string?               @description(#"Automation/agent/tool ID"#)

    guard string?                 @description(#"Boolean expression gating execution"#)
}

class ConstrainedTaskGraph {
    tasks ConstrainedTask[]?                  @description(#"All tasks (can include multiple roots)"#)
    roots string[]?               @description(#"Optional; else infer as tasks with no inbound deps"#)
    edges DataEdge[]?             @description(#"Typed dataflow across tasks; also implies ordering"#)
}

function GenerateConstrainedTaskGraph(in_arg: string) -> ConstrainedTaskGraph {
    client CustomGPT4oMini
    prompt #"
        Generate the execution path for the given string. If the main task is not applicable there is no need to generate subtasks
        {{ctx.output_format}}
        ------ GIVEN STRING ------
        {{in_arg}}
        ------ END GIVEN STRING ------        
    "#
}
