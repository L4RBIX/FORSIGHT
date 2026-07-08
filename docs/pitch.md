# FORESIGHT - Pitch

Robots should not discover danger by breaking things.

Foresight is a predictive safety layer for physical AI. Before a robot moves, it builds a world model, simulates the requested action under uncertainty, estimates the risk of physical failure, and returns ALLOW or BLOCK.

The key difference is grounding: the final safety decision comes from physics-based outcomes, not from a language model guess.

## Demo claim

Given a tabletop scene with a blue box and a mug near the edge, Foresight predicts that pushing the box right will likely knock the mug off the table. It blocks the action before the robot moves.

## Why it matters

Home robots, warehouse arms, and service robots increasingly operate near people and fragile objects. Static safety zones are not enough when the whole point is to interact with the real world.

Foresight gives robots a short-term physical imagination.
