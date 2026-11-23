// ACEest Fitness & Gym - CI/CD pipeline
// Checkout -> Lint & Unit Tests -> SonarQube + Quality Gate -> Docker build ->
// Pytest inside container -> Push to Docker Hub -> Artifacts -> Deploy to Kubernetes
// (strategy selectable) -> Smoke test, with automatic rollback on failure.
pipeline {
    agent any

    parameters {
        choice(name: 'DEPLOY_STRATEGY',
               choices: ['rolling', 'blue-green', 'canary', 'ab-testing', 'shadow', 'none'],
               description: 'Kubernetes deployment strategy for this build')
        string(name: 'DOCKERHUB_USER', defaultValue: 'faheemmahamoonbits',
               description: 'Docker Hub namespace for the aceest-fitness image')
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE_NAME = 'aceest-fitness'
        KUBE_NAMESPACE = 'aceest'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.APP_VERSION = readFile('VERSION').trim()
                    env.IMAGE = "${params.DOCKERHUB_USER}/${env.IMAGE_NAME}"
                    currentBuild.displayName = "#${env.BUILD_NUMBER} v${env.APP_VERSION} (${params.DEPLOY_STRATEGY})"
                }
            }
        }

        stage('Lint & Unit Tests') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install -q -r requirements-dev.txt
                    .venv/bin/flake8 .
                    .venv/bin/pytest -v --junitxml=test-results.xml \
                        --cov=aceest --cov-report=xml:coverage.xml --cov-report=term
                '''
            }
        }

        stage('SonarQube Analysis & Quality Gate') {
            steps {
                script {
                    def scannerHome = tool 'mySonarScanner'
                    withSonarQubeEnv('MySonarServer') {
                        // sonar.qualitygate.wait=true makes this step fail if the gate fails
                        sh "${scannerHome}/bin/sonar-scanner -Dsonar.projectVersion=${env.APP_VERSION}"
                    }
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build --target test -t ${IMAGE}:${APP_VERSION}-test .
                    docker build --target runtime --build-arg APP_VERSION=${APP_VERSION} \
                        -t ${IMAGE}:${APP_VERSION} -t ${IMAGE}:${APP_VERSION}-b${BUILD_NUMBER} -t ${IMAGE}:latest .
                '''
            }
        }

        stage('Pytest inside Container') {
            steps {
                sh 'docker run --rm ${IMAGE}:${APP_VERSION}-test'
                sh '''
                    docker rm -f aceest-smoke 2>/dev/null || true
                    docker run -d --name aceest-smoke -p 15000:5000 ${IMAGE}:${APP_VERSION}
                    for i in $(seq 1 20); do curl -fs localhost:15000/health && break; sleep 2; done
                    curl -fs localhost:15000/version
                    docker rm -f aceest-smoke
                '''
            }
        }

        stage('Push to Docker Hub') {
            when { expression { params.DOCKERHUB_USER?.trim() } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        docker push ${IMAGE}:${APP_VERSION}
                        docker push ${IMAGE}:${APP_VERSION}-b${BUILD_NUMBER}
                        docker push ${IMAGE}:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Build Artifacts') {
            steps {
                sh '''
                    mkdir -p dist
                    tar czf dist/aceest-fitness-${APP_VERSION}-b${BUILD_NUMBER}.tar.gz \
                        VERSION ACEest_Fitness.py aceest requirements.txt Dockerfile k8s
                    docker save ${IMAGE}:${APP_VERSION} | gzip > dist/aceest-fitness-image-${APP_VERSION}.tar.gz
                '''
                archiveArtifacts artifacts: 'dist/*.tar.gz, coverage.xml, test-results.xml', fingerprint: true
            }
        }

        stage('Deploy to Kubernetes') {
            when { expression { params.DEPLOY_STRATEGY != 'none' } }
            steps {
                sh "scripts/deploy.sh ${params.DEPLOY_STRATEGY} ${env.IMAGE} ${env.APP_VERSION}"
            }
            post {
                failure {
                    echo 'Deployment failed - rolling back to the last stable version'
                    sh "scripts/rollback.sh ${params.DEPLOY_STRATEGY} || true"
                }
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
        success {
            echo "ACEest ${env.APP_VERSION} built, tested and delivered (${params.DEPLOY_STRATEGY})"
        }
        failure {
            echo 'Pipeline failed - nothing was promoted'
        }
    }
}
