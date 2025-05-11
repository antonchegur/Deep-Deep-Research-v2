---
description: 
globs: 
alwaysApply: false
---
- **Update tasks.md After Implementing Project Tasks**
  - After completing a task or subtask, update the status in tasks.md
  - When starting a new task, mark it as "in-progress" in tasks.md
  - Run `task-master list` and `task-master complexity-report` to get the latest task data

- **Required Sections for tasks.md**
  - **Project Tasks Table**: Include ID, Title, Status, Priority, Dependencies, and Complexity
  - **Project Status Summary**: Show total count and completion percentage
  - **Completed Subtasks**: List all completed subtasks with their details
  - **Next Tasks to Focus On**: Identify 2-3 next tasks based on dependencies and priority
  - **Complexity Analysis Notes**: Highlight the most complex tasks

- **Status Indicators**
  - Use emoji for better visual scanning:
  ```markdown
  | Status | Indicator |
  |--------|-----------|
  | done | ✅ done |
  | in-progress | 🔄 in-progress |
  | pending | ⏱️ pending |
  | review | 👀 review |
  | blocked | ❌ blocked |
  ```

- **Example Format**
  ```markdown
  # Deep Deep Research v2 - Task List

  *Updated: [Current Date]*

  ## Project Tasks

  | ID | Title | Status | Priority | Dependencies | Complexity |
  |----|-------|--------|----------|--------------|------------|
  | 1 | Project Setup | ✅ done | high | - | - |
  | 2 | Core Development | ✅ done | high | - | - |
  | 3 | GPT-4 Integration | 🔄 in-progress | high | 1 | 8/10 |
  ```

- **Automating Updates**
  - Consider writing a script that pulls data from `task-master` and updates tasks.md
  - Example script structure:
  ```bash
  #!/bin/bash
  # Update tasks.md based on current task-master state
  echo "Updating tasks.md..."
  task_data=$(task-master list --json)
  complexity_data=$(task-master complexity-report --json)
  # Process data and generate markdown...
  ```

- **Reference Current Example**
  - See the existing [tasks.md](mdc:tasks.md) for an implementation example
  - This file shows the expected structure and format for task documentation

- **Keeping timestamps current**
  - Always update the timestamp at the top of the file
  - Format: *Updated: Month, Year* (e.g., *Updated: May, 2025*)
