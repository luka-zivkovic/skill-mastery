.PHONY: check test doctor audit start new-skill demo

# One command to verify the toolkit is healthy.
check doctor:
	python3 scripts/doctor.py

test:
	python3 -m unittest discover -s tests

# Audit the skills in this repo (point at any path to audit another).
audit:
	python3 scripts/audit_skills.py .

# Guided first-run summary for this repo (point ROOT at another repo).
start:
	python3 scripts/start.py $${ROOT:-.} --no-inventory

# Create a workshop draft: make new-skill NAME=my-skill DESCRIPTION='Use when...'
new-skill:
	@test -n "$$NAME" || (echo "Usage: make new-skill NAME=my-skill DESCRIPTION='Use when...'" && exit 1)
	@test -n "$$DESCRIPTION" || (echo "DESCRIPTION is required; include trigger conditions" && exit 1)
	python3 scripts/create_skill.py "$$NAME" --description "$$DESCRIPTION" \
		--kind "$${KIND:-claude}" --resources "$${RESOURCES:-}"

# Run the full SkillOpt loop offline (deterministic mock adapter).
demo:
	python3 scripts/skillopt_run.py examples/toy-skill examples/toy-evals/eval-manifest.yaml \
		--adapter mock --epochs 3 --out workshop/runs
