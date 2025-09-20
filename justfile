# Git worktree management commands

# Create a new worktree with automatic branch creation (enhanced wt function)
wt branch:
    #!/usr/bin/env bash
    if git worktree list | grep -q "{{branch}}"; then
        echo "Worktree {{branch}} already exists"
        exit 1
    fi
    mkdir -p ../worktrees
    git worktree add ../worktrees/{{branch}} main
    cd ../worktrees/{{branch}} && git checkout -b {{branch}}
    echo "Created worktree: ../worktrees/{{branch}}"
    echo "To enter: cd ../worktrees/{{branch}}"

# Create a new worktree for a branch (original version)
create-worktree branch path:
    git worktree add {{path}} {{branch}}

# Close/remove a specific worktree
close-worktree path:
    git worktree remove {{path}}

# Push branch and create PR, then close worktree
push-and-close branch:
    #!/usr/bin/env bash
    cd ../worktrees/{{branch}}
    git push -u origin {{branch}}
    echo "Pushed branch {{branch}} to remote"
    echo "Create PR manually or use: gh pr create --title 'Your title' --body 'Your description'"
    cd - > /dev/null
    git worktree remove ../worktrees/{{branch}}
    echo "Closed worktree: ../worktrees/{{branch}}"

# Merge branch to main and close worktree
merge-and-close branch:
    #!/usr/bin/env bash
    git checkout main
    git merge {{branch}}
    git worktree remove ../worktrees/{{branch}}
    echo "Merged {{branch}} to main and closed worktree"
    echo "Don't forget to: git push origin main"

# Clean up all non-main worktrees (enhanced wtc function)
wtc:
    #!/usr/bin/env bash
    main_worktree=$(git rev-parse --show-toplevel)
    git worktree list --porcelain | \
    grep -B2 "branch refs/heads/" | \
    grep "worktree" | \
    grep -v "$main_worktree" | \
    cut -d' ' -f2 | \
    xargs -I {} git worktree remove {}
    echo "Cleaned up all feature worktrees"

# List all worktrees
list-worktrees:
    git worktree list

# Prune deleted worktrees
prune-worktrees:
    git worktree prune