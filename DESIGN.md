# FlyBrain Observatory Design

## Direction

The interface is a living specimen chamber: a large dark observation field with
a restrained scientific instrument rail. It shows measurements and motion, not
narrative claims about thought or consciousness.

## Tokens

| Role | Value |
| --- | --- |
| Chamber black | `#070b0f` |
| Optical slate | `#14202a` |
| Specimen cyan | `#58d6d0` |
| Food amber | `#f2b84b` |
| Motor/neural magenta | `#e36da6` |
| Paper white | `#e8efef` |
| Corners | 12-14 px |
| Motion | 140 ms interaction, 300 ms state, 650 ms reveal |
| Easing | `cubic-bezier(0.2, 0, 0, 1)` |

Persian uses the local system font stack; official identifiers and readings use
the system monospace stack. No remote fonts or tracking resources are loaded.

## Layout and behavior

Desktop places the dominant chamber on the right, instruments on the left, and
active neurons below the chamber. Under 900 px the chamber, instruments, and
activity list stack. Under 560 px the instruments become a single column and
the camera follows the fly horizontally so it is not clipped.

Cyan means sensory/world trace, amber means food/hunger, and magenta means motor
or neural activity. Pause/resume is the single primary action. Reduced-motion
preference removes flutter and reveal animation. All visible browser copy is
Persian except stable technical identities that must remain exact.
