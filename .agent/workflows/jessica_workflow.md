---
description: Jessica AI - Comprehensive System Workflow
---

# Jessica AI System Workflow

This document outlines the complete workflow for Jessica AI, connecting Frontend, Backend, Search, and Continuous Learning.

## 1. User Interaction Flow (Frontend <-> Brain <-> Search)

**Goal**: Respond to user queries using internal knowledge (Brain) and external information (Search Engine).

1.  **User Input**: User types a message in the **Frontend** (Desktop UI or Web UI).
2.  **Processing (Brain)**:
    *   The message is sent to the `Brain` core (`src/core/brain.py`).
    *   **Context Injection**: The Brain injects the "Jessica" persona.
    *   **Heuristic Check**: The Brain checks if the input matches a tool pattern:
        *   `"search <query>"` -> Calls **Search Engine** (`google_search` in `src/backend/ai_core.py`).
        *   `"run command <cmd>"` -> Calls **Shell Tool**.
        *   `"read file <path>"` -> Calls **File System Tool**.
    *   **RAG Lookup**: If not a tool, it checks **Vector Memory** (Supabase) for relevant context.
3.  **Response Generation**:
    *   If a tool was used (e.g., Search), the tool output IS the response.
    *   If no tool, the `JessicaGPT` local model (or Cloud Fallback) generates a reply using the context.
4.  **Display**: The response flows back to the Frontend.

## 2. Continuous Learning Flow (Isolated)

**Goal**: Autonomously learn new topics 24/7 without slowing down the main interaction.

1.  **Execution**: Runs as a **separate process** via `start_training.bat`.
2.  **Cycle (`src/backend/continuous_learning.py`)**:
    *   **Topic Selection**: Picks a topic from the priority list (Security, Tech).
    *   **Research**: Performs a Google/DDG Search.
    *   **Deep Dive**: Crawls top URLs to extract content.
    *   **Memorization**:
        *   Embeds content into **Vector Store** (Supabase).
        *   Archives raw data to Cloud Storage.
3.  **Independence**: This loop runs in its own window. It interacts with the *Database*, not the *Frontend*, so the User never experiences lag.

## 3. Connectivity Diagram

```mermaid
graph TD
    User[User] -->|Chat| UI[Frontend (Desktop/Web)]
    UI -->|Input| Brain[Brain Core]
    
    subgraph "Interaction Workflow"
        Brain -->|Check| Heuristics{Tool?}
        Heuristics -->|Yes: 'search'| Search[Search Engine (Google/DDG)]
        Heuristics -->|Yes: 'exec'| Shell[Shell]
        Heuristics -->|No| Model[JessicaGPT / Cloud]
        
        Search -->|Results| Brain
        Model -->|Reply| Brain
    end
    
    subgraph "Continuous Training Workflow (Independent)"
        Trainer[Continuous Learner] -->|1. Pick Topic| Search2[Search Engine]
        Search2 -->|2. Crawl| Web[Web Pages]
        Web -->|3. Store| DB[(Supabase Vector DB)]
    end
    
    Brain -->|RAG Lookup| DB
    Trainer -.->|No Interference| User
```

## How to Run

1.  **Main Application**: Run `Run.bat`.
2.  **Continuous Training**: Run `start_training.bat` in a separate window.
