# ACEest Fitness & Gym — End-to-end CI/CD (Assignment 2)

Flask application for ACEest Fitness & Gym delivered through a fully automated pipeline:
**Git/GitHub → Jenkins → Pytest → SonarQube → Docker → Docker Hub → Kubernetes (Minikube)**, with
Rolling Update, Blue-Green, Canary, A/B Testing and Shadow deployments plus rollback.

## Repository layout

```
ACEest_Fitness.py        WSGI entry point (ACEest_Fitness:app)
aceest/                  Flask package, one blueprint per feature/version
tests/                   Pytest suite (one file per feature)
legacy/                  The provided desktop versions (Aceestver-*.py) for reference
VERSION, CHANGELOG.md    Current version and version history
Dockerfile               Multi-stage: test image + slim non-root runtime image
Jenkinsfile              CI/CD pipeline (Poll SCM)
sonar-project.properties SonarQube analysis + quality gate
k8s/                     Kubernetes manifests per deployment strategy
scripts/                 deploy, rollback, canary promotion, traffic checks, VM setup
docs/                    Report and SonarQube report
```

## Versions

Every desktop version is reimplemented as a Flask release and tagged (`v1.0` … `v3.2.4`); see
[CHANGELOG.md](CHANGELOG.md). Images: `<dockerhub-user>/aceest-fitness:<version>`.

Branching: `main` is always releasable; work happens on `feature/*`, `fix/*`, `infra/*` and
`docs/*` branches merged with `--no-ff`, and each release is an annotated tag.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python ACEest_Fitness.py                 # http://localhost:5000
pytest -v --cov=aceest                   # unit tests + coverage
docker build --target runtime -t aceest-fitness . && docker run -p 5000:5000 aceest-fitness
```

Key endpoints: `/health`, `/version`, `/programs`, `/clients`, `/clients/<name>/progress`,
`/clients/<name>/workouts`, `/bmi`, `/login`, `/clients/<name>/report`, `/clients/<name>/membership`.

## Pipeline (Jenkinsfile)

1. **Checkout** (Poll SCM every 2 min) and read `VERSION`
2. **Lint & Unit Tests** – flake8 + pytest with JUnit and coverage reports
3. **SonarQube Analysis & Quality Gate** – build fails if the gate fails
4. **Docker Build** – test image and runtime image (`<version>`, `<version>-b<build>`, `latest`)
5. **Pytest inside Container** + container smoke test on `/health`
6. **Push to Docker Hub** (credential `dockerhub-creds`)
7. **Build Artifacts** – versioned source bundle, image tarball, test reports (archived)
8. **Deploy to Kubernetes** with the `DEPLOY_STRATEGY` parameter; automatic rollback on failure

Jenkins needs: SonarQube server `MySonarServer`, scanner tool `mySonarScanner`, credential
`dockerhub-creds`, and Docker/kubectl access (`scripts/vm-setup.sh`).

## Deployment strategies (namespace `aceest`, ingress-nginx)

| Strategy | Manifests | Host | How it works | Rollback |
|---|---|---|---|---|
| Rolling Update | `k8s/rolling` | rolling.aceest.local | pods replaced one by one, `maxUnavailable: 0` | `kubectl rollout undo` |
| Blue-Green | `k8s/blue-green` | bluegreen.aceest.local | new colour deployed + tested, Service selector switched | switch selector back |
| Canary | `k8s/canary` | canary.aceest.local | ingress canary weight (default 20%) | delete canary ingress |
| A/B Testing | `k8s/ab-testing` | ab.aceest.local | header `X-Variant: B` / cookie `ab_variant=always` → B | delete variant-B ingress |
| Shadow | `k8s/shadow` | shadow.aceest.local | requests mirrored to shadow, responses discarded | remove mirror annotation |

```bash
scripts/deploy.sh canary <user>/aceest-fitness 3.2.4      # STABLE_TAG=3.1.2 by default
scripts/traffic-check.sh canary.aceest.local 50            # count versions answering
scripts/traffic-check.sh ab.aceest.local 10 -H "X-Variant: B"
scripts/rollback.sh canary
```

On the Prayogshala VM run `scripts/vm-setup.sh` once per session (it uses sudo).
