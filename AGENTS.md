# Shared repository workflow

- The shared source of truth is https://github.com/GarvGupta25/Helm_AI. The owner and a friend both work in this repository.
- Before starting work, inspect the current branch and local changes, fetch origin, and pull the latest branch updates with `git pull --ff-only` when the working tree permits it. Preserve existing local work and collaborators' changes.
- Make the smallest complete change and run the checks appropriate to it. Use the root README for the prototype setup and isolated demo API.
- When work is finished, commit only the intended files, fetch again, integrate any new remote changes, and push the finished commits to this repository. Do not leave completed changes only on the local machine.
- Never force-push shared history or commit credentials, local environment files, runtime databases, or generated dependency folders. Report a blocked push clearly.
