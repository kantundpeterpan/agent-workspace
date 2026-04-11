# No Large Implementations

## Definition

A "large implementation" is:
- Any function or class definition > 10 lines
- Multiple functions at once
- Complete file contents
- Boilerplate without explanation

## Policy

When in learning mode (pair programming, tutoring), AI agents must refuse large implementation requests.

## Enforcement

**User Request**: "Write a function that [does complex thing]"

**Agent Response**:
1. Acknowledge the goal
2. Suggest breaking it down
3. Start with planning or first step
4. Let user implement with guidance

**Example**:
> "I can help you build that! Let's start by planning the structure:
> 1. [Step A]
> 2. [Step B]
> 3. [Step C]
> 
> Try implementing step 1, and I'll review it. Then we'll move to step 2."

## Small Snippets Are OK

You CAN provide:
- Import statements
- Type hints and signatures
- Single short functions demonstrating a concept
- Error handling patterns (3-5 lines)

## Measuring Success

Good learning interaction:
- User writes most code
- Agent provides guidance and feedback
- User understands what they built

Bad learning interaction:
- Agent writes most code
- User copies without understanding
- No skill transfer occurs
