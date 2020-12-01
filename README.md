# CloudNative Python Flask API

This repository contains a demo of a Python Flask API that was developed in 3 hours as a cloud native application. This API takes a JSON containing a string, reverse it and convert it to all capitals using an external API.

## Running the app locally

You can test the app locally using the provided Dockerfile

First, build the image

```
docker build . -t flask-api
```

Run the image 

```
docker run -p 5000:5000 flask-api
```

And test it with a curl command

```
curl --header "Content-Type: application/json" -X POST -d '{"data": "hello, world!"}' http://localhost:5000/v1
```

## Deployment to k8s

I'm using Ansible to deploy to AWS EKS. I have created the cluster with eksctl. In the real world I would use Terraform or Ansible, for this eksctl is the quickest way to do it, so I went with this method for the quick demo.


Add environment variables to your deploying machine:

```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export ECR_URL=
```

Create cluster

```
eksctl create cluster \
 --name sre-take-home-eks \
 --version 1.18 \
 --with-oidc \
 --without-nodegroup \
 --region=us-east-2
```

Create nodegroup:

```
eksctl create nodegroup \
  --cluster sre-take-home-eks \
  --version auto \
  --name nodes \
  --node-type t3.medium \
  --node-ami auto \
  --nodes 1 \
  --nodes-min 1 \
  --nodes-max 1 \
  --region=us-east-2
```

To build and deploy the application I'm using a simple Ansible Playbook

To run the Ansible Playbook

```
ansible-playbook aws-deployment.yml
```

You should see an output similar to this:

```
agus@XPS13:/mnt/c/Users/Agus/flask-demo$ ansible-playbook aws-deployment.yml
[WARNING]: No inventory was parsed, only implicit localhost is available
[WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match
'all'

PLAY [Deploy AWS infrastructure and code] ******************************************************************************

TASK [Login into ECR] **************************************************************************************************
changed: [localhost]

TASK [Create repo] *****************************************************************************************************
ok: [localhost]

TASK [Login into EKS cluster] ******************************************************************************************
changed: [localhost]

TASK [Create namespace] ************************************************************************************************
ok: [localhost]

TASK [Create Deployment] ***********************************************************************************************
changed: [localhost]

TASK [Create Service] **************************************************************************************************
ok: [localhost]

PLAY RECAP *************************************************************************************************************
localhost                  : ok=6    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

After running the Ansible Playbook, there should be a deployment in the cluster in the flask-api namespace:

```
~$  kubectl get deployment
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
flask-api   3/3     3            3           6m45s
```

And 3 pods should be running:

```
NAME                         READY   STATUS    RESTARTS   AGE
flask-api-6884d947bb-8skjh   1/1     Running   2          35s
flask-api-6884d947bb-nzhst   1/1     Running   2          35s
flask-api-6884d947bb-tmp95   1/1     Running   2          35s
```

Log output of one of the pods:

```
~ $ kubectl logs flask-api-6884d947bb-8skjh
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 996-489-439
```

The deployment also includes a k8s service that publish the port 5000 of the containers and perform load balancing:

```
~$ kubectl describe svc flask-service
Name:              flask-service
Namespace:         flask-api
Labels:            <none>
Annotations:       <none>
Selector:          app=flask-api
Type:              ClusterIP
IP:                10.100.62.170
Port:              <unset>  5000/TCP
TargetPort:        5000/TCP
Endpoints:
Session Affinity:  None
Events:            <none>
```

## What extra steps I would have taken to put this into production 

In no specific order, here are some of the things that I would have done to take this to production if this was a real application

### Put the app behind a reverse proxy

Most of the time REST APIs are running behind a reverse proxy. I usually use NGINX. Specifically in k8s, now I usually take advantage of the [NGINX Ingress Controller](https://github.com/kubernetes/ingress-nginx)

### Authentication 

Asuming that this API is open to the public, I would add so kind of authentication. [Amazon Cognito](https://aws.amazon.com/cognito/) is great.

### Make the deployment part of a CI/CD pipeline

I would have trigger unit tests with any PRs that developers open. Once the PR is merged into the integration branch, I would trigger the deployment code deploying to the staging environment, running integrations tests after that and finally deploying to production after manual validation (or no) depending on internal policies. 

### k8s RBAC

Obviously I haven't had time, but I would define multiple RBAC policies in the EKS cluster to control access to different teams

### Integration with a logging aggregation system

I would have followed a sidecard pattern where a [Filebeat](https://www.elastic.co/beats/filebeat) container runs alongside the Flask container, reading logs and injecting them in an [ELK stack](https://www.elastic.co/what-is/elk-stack) where we can consult them in Kibana and define different aggregation and analysis rules.

### Integration with some monitorig system

I have defined a livenessProbe in the k8s deployment that would allow for some selfhealing behaviour, as well as 3 replicas which should provide some HA capabilities, but all of that doesn't mean much without a monitoring solution. I would have done some basic monitoring using [CloudWatch](https://aws.amazon.com/cloudwatch/)

### Cleanup app.py

I have done some shaddy coding because of time constrains. I would have done some things with more time or a better development environment, including:

* I would simplify the code using less transactional variables.
* Load configuration variables from environment variables in the container like the SHOUTCLOUD endpoint URL.
* Pin version libraries in the requirements.txt instead of always using the latest version.
* Do some basic unit testing
* Use a string input instead of JSON (sorry, I cheated on this one a bit, my Flask is a bit rusty and I couldn't get a string to work, so I went with JSON, shame on me).

### Improve the deployment code

Some things that I'm missing:

* Create the infrastructure as IaC with Terraform or Ansible instead of using eksctl to create the EKS cluster.
* Clean up authentication with AWS in the Ansible Playbook. Load variables once instead of using them on each task.
* Tag images with the hash of git commit so each artifact have a 1:1 relationship with specific versions of the code.