pipeline {
    agent any

    environment {
        AWS_REGION = "us-east-1"
        S3_BUCKET = "fotographiya-ai-photo-bucket"
    }

    stages {
        stage('Clone Repository') {
            steps {
                git url: 'https://github.com/mysticharshuuu45/terraform-cicd-task_jenkins.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'sudo apt update && sudo apt install -y python3-pip'
                sh 'pip3 install pillow boto3'
            }
        }

        stage('Run AI Processing') {
            steps {
                sh 'python3 app.py'
            }
        }
    }

    post {
        success {
            echo "Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline failed!"
        }
    }
}
