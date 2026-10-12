# AI Usage Documentation

**Course:** Software Engineering with AI  
**Project:** Mario Kart Player Performance Analysis  
**Updated:** October 11, 2026

## Purpose

This document describes how artificial intelligence tools have supported the development of our project. AI is used as an assistant for learning, planning, coding, testing ideas, and documentation. Its suggestions are not automatically accepted as correct.

## AI Tools Used

### 1. ChatGPT (OpenAI)

We have used ChatGPT for conversational assistance throughout the project, including:

- **Planning and design:** Discussing how to organize the project and approach Mario Kart player-performance analysis.
- **Programming support:** Asking questions about C# backend files, application structure, and possible implementation approaches.
- **Troubleshooting and explanations:** Working through programming concepts, errors, and unfamiliar development workflows.
- **Testing and GitHub workflow:** Clarifying expectations for unit tests, test coverage, pull requests, and peer review.
- **Documentation:** Helping organize and draft this AI-usage document.

ChatGPT's responses serve as explanations and suggestions. We are responsible for deciding what belongs in the project.

### 2. GitHub Copilot (Visual Studio Code)

We use GitHub Copilot as an AI programming assistant in Visual Studio Code. Its role in the development workflow is to support writing and understanding code through in-editor suggestions and coding assistance. Relevant uses include:

- Suggesting completions and possible implementations while editing code.
- Helping explain code and offering possible improvements.
- Supporting debugging, refactoring, and the development of tests when requested.

## Representative AI-Assisted Tasks

The following are examples of the types of questions and tasks for which AI assistance has been useful. They are paraphrases, not a verbatim prompt transcript.

| Task | AI tool | Example of assistance |
| --- | --- | --- |
| C# project organization | ChatGPT | Understanding which backend files belong in the GitHub repository, including `Program.cs`, service classes, and `.csproj` files. |
| Implementation | ChatGPT / Copilot | Considering how backend code and a performance-analysis service should be organized. |
| Testing expectations | ChatGPT | Understanding what unit-test coverage means and how an 80% coverage requirement should be demonstrated. |
| GitHub collaboration | ChatGPT | Clarifying pull-request submission and teammate-review requirements. |
| Code editing | Copilot in VS Code | Receiving in-editor programming suggestions to consider and review. |
| Documentation | ChatGPT | Helping draft, organize, and revise documentation files throughout the repository for team review. |

## Review and Validation

AI-generated text or code may contain mistakes, make incorrect assumptions, or fail to meet the assignment requirements. For that reason, our development workflow should include:

1. Comparing suggestions with the assignment and project requirements.
2. Reading and understanding suggested code before accepting it.
3. Compiling and running the application to identify problems.
4. Running relevant unit or integration tests and reviewing actual results.
5. Measuring test coverage with the project's coverage tool rather than assuming a target was reached.
6. Using teammate review for pull requests where required.

The team remains responsible for the final code, testing evidence, design decisions, and submission.

## Additional AI Tool Considered (Not Yet Used)

**CodeRabbit** — https://www.coderabbit.ai/  
CodeRabbit is an AI code-review tool that can review code changes in VS Code and GitHub pull requests. It may be helpful for identifying possible defects, questionable changes, and missing tests. It is listed as a **potential future tool**, not as a tool already used on this project. If the team begins using it, we will update this document to describe the actual reviews performed and any changes made in response.

## AI Contribution Statement

AI tools have assisted with explanations, planning, code suggestions, development workflow questions, and documentation. AI output is reviewed rather than treated as authoritative, and responsibility for the submitted work remains with the student team.
