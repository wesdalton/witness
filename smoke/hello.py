"""Step 0: the smallest possible task, used to prove the toolchain works end to end.

    inspect eval smoke/hello.py --model <provider/model>
"""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import includes
from inspect_ai.solver import generate


@task
def hello() -> Task:
    return Task(
        dataset=[Sample(input="Reply with exactly the word: pong", target="pong")],
        solver=generate(),
        scorer=includes(),
    )
