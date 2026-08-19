## 1. Proxy /jenkins/ through to the prefixed Jenkins

- [x] 1.1 In `nginx/nginx.conf`, change the `location /jenkins/` `proxy_pass` to `http://jenkins:8080/jenkins/`
- [x] 1.2 Delete the `sub_filter*`, `proxy_redirect`, and `Accept-Encoding ""` lines from the `/jenkins/` block
- [x] 1.3 Confirm the `Host` and `X-Forwarded-For`/`X-Forwarded-Proto`/`X-Forwarded-Prefix` headers remain set

## 2. Point the Django Jenkins client at the prefixed base URL

- [x] 2.1 In `jenkins_config.py`, append `/jenkins` to `JENKINS_SERVER_URL`
- [x] 2.2 Confirm no other backend module constructs a root-path Jenkins base URL

## 2b. Point the container startup scripts at the prefixed base URL

The webapp entrypoint `wait-for-db.sh` gates Django startup on Jenkins readiness and bootstraps
jobs. These scripts build their own root-path Jenkins URL and must include the prefix.

- [x] 2b.1 In `ping_jenkins.py`, append `/jenkins` to `JENKINS_SERVER_URL` (startup readiness gate)
- [x] 2b.2 In `configure_jenkins.py`, append `/jenkins` to `JENKINS_SERVER_URL`
- [x] 2b.3 In `add_jenkins_job.py`, append `/jenkins` to `JENKINS_SERVER_URL`
- [x] 2b.4 Confirm the pod startup gate passes (Jenkins reachable) and Django boots (no 502)

## 3. Terminate TLS only at nginx

- [ ] 3.1 In the k8s deployment manifests, configure Jenkins to serve plain HTTP on 8080 (drop `--httpsPort`/keystore)
- [ ] 3.2 Remove the `:8443` service/port exposure and the JKS keystore mount for Jenkins
- [ ] 3.3 Confirm nginx forwards `X-Forwarded-Proto=https` so Jenkins advertises https external URLs

## 4. Verify end-to-end (coordinated with nita-jenkins)

- [ ] 4.1 Deploy the `nita-jenkins` `jenkins-path-prefix` image change together with this change
- [x] 4.2 Verify `https://<host>/jenkins/login` renders fully with no missing assets
- [ ] 4.3 Verify triggering an action returns 202 and the SSE console stream works
- [x] 4.4 Verify the SPA Jenkins deep-links (`/jenkins/job/...`) open the correct job/build pages
- [x] 4.5 Grep this repo for `jenkins:8080`/`:8443` root-path usage and confirm each caller uses `/jenkins`
