# Blender LLM Spatial Middleware

**Overcoming Spatial Reasoning Limitations in Small Language Models for 3D Environments**

## The Problem
Local Large Language Models (e.g., 6.7B parameter models like DeepSeek Coder) are highly capable of generating code but struggle significantly with 3D spatial mathematics. When prompted to move objects in a 3D workspace, they fail to calculate complex vectors and default to global X/Y/Z axes, ignoring the user's actual viewport perspective. Relying on an LLM for raw mathematical calculation in a 3D engine leads to hallucinations and structural breakdowns.

## The Solution: Tool Calling Architecture
This project solves the spatial reasoning limit by shifting the mathematical burden from the LLM to a hardcoded Python middleware layer. Using a strict "Tool Calling" paradigm, the LLM is heavily restricted via system prompts. It is forbidden from writing raw math or looping logic. Instead, it acts merely as a routing agent that extracts parameters (Object, Target, Direction, Distance) and triggers pre-written, highly optimized Python functions.

## Core Features

*   **Viewport-Relative Translation:** The script fetches the user's current 3D viewport angle and calculates directional vectors (Left, Right, Up, Down, Front, Behind) relative to that specific view matrix. 
*   **Matrix Inversion Mathematics:** Utilizes `view_matrix.inverted().to_3x3()` to seamlessly convert view space directional vectors back into world space coordinates.
*   **Target-Based Relative Positioning:** Capable of calculating movement relative to a secondary reference object in the scene before applying the directional vector.
*   **Case-Insensitive Object Targeting:** Bypasses Blender's strict string-matching constraints, allowing the LLM to find objects regardless of capitalization errors.
*   **Autonomous Instantiation:** Includes tools for the LLM to spawn primitive geometry directly into the scene.

## Technical Implementation (How it Works)
1. **User Input:** The user types a natural language command in the custom Blender UI panel (e.g., *"Move the cone 2 meters to the left of the cube"*).
2. **LLM Parsing:** The local LLM processes the text and outputs a strictly formatted tool call: `move_a_relative_to_b("cone", "cube", "Left", 2.0)`
3. **Middleware Execution:** The string is executed securely within a restricted `exec_globals` dictionary.
4. **Vector Math:** The Python backend calculates the exact world space destination using the camera's inverted view matrix and updates the object's location instantly.

## Tech Stack
*   **Environment:** Blender 3D / `bpy` (Blender Python API)
*   **AI Backend:** Local LLM via REST API (Ollama / DeepSeek Coder 6.7B)
*   **Core Math:** `mathutils.Vector`, Matrix transformations.