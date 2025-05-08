# #!/bin/bash

# # Create Docker network
# docker network create test_db

# # Run the main service container with environment variables from the secret
# docker run -dit --name ks_service_nest --network test_db \
#   -e DATABASE_NAME=ks_dev_cluster_knowledgesearch_db_sql \
#   -e DATABASE_USERNAME=masterUsersql \
#   -e DATABASE_HOST=ks-db-dev.cvwkkmau6qnx.us-west-2.rds.amazonaws.com \
#   -e PYTHONPATH=/app \
#   -e DEBUG=True \
#   -e AUTH_KAAS_CLIENT_SECRET=byf9T3wXXcCljGKcPAWxs9sxow4EAA2J \
#   -e AUTH_DOCCEBO_PASSWORD=5w62992 \
#   -e AUTH_OPENSEARCH_PASSWORD=K3!0dg_7Hc \
#   -e AUTH_KZ_CLIENT_SECRET=aqfr1drih5k1ttdi6jq7oej9355ru37s \
#   -e AUTH_UID_CLIENT_SECRET=3euNa1Aty0tPN7d9mW1Y3BCFOAcHZbnTHNf1ifoMQmBHTztInM5mm03vkyp8C570 \
#   -e AUTH_API_SERIVCE_E2E_CLIENT_SECRET=gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v \
#   -w /app \
#   -e DATABASE_PORT=3306 \
#   -e DATABASE_PASSWORD=3cQHw1JbDdG4 \
#   -e DATABASE_SYNC=false \
#   -e DATABASE_LOGGING=true \
#   -e DATABASE_USE_CERT=false \
#   $2

# # Check if the container is running
# echo "Running container: $(docker ps -a)"
# sleep 30
# container_status=$(docker inspect -f '{{.State.Status}}' ks_service_nest)
# echo "Container status: $container_status"

# if [ "$container_status" != "running" ]; then
#     echo "Container is not running. Fetching logs for diagnosis..."
#     docker logs ks_service_nest
#     exit 1
# fi

# # Activate the virtual environment and execute test cases inside the running container
# echo "Executing test cases"
# docker exec -i ks_service_nest /bin/sh -c ". /opt/env/bin/activate && pytest" || { echo "Test execution failed"; exit 1; }

# # Verbose test execution
# docker exec -i ks_service_nest /bin/sh -c ". /opt/env/bin/activate && pytest"

# docker exec -i ks_service_nest report run -m pytest -v
# docker exec -i ks_service_nest report.html
# # Output the current directory and list files in the container
# echo "PWD & Listing files"
# docker exec -i ks_service_nest pwd
# docker exec -i ks_service_nest ls -larth

# # List files in the app directory
# echo "PWD & Listing files in /app"
# docker exec -i ks_service_nest ls -larth /app/
# docker exec -i ks_service_nest ls -larth /app/app
# docker exec -i ks_service_nest ls -larth /ks_service_nest/app
# #docker exec -i ks_service_nest ls -larth /app/app/controllers
# docker exec -i ks_service_nest cat /app/report.html

# # Display the content of the report file (if exists)
# docker exec -i ks_service_nest cat /app/report.html || echo "No report.html found"

# # Create output directory on the host
# echo "Creating output directory"
# mkdir -p $3/report/
# ls -larth $3/

# # Copy the test report to the output directory
# echo "Copying the test report"
# docker cp ks_service_nest:/app/report.html $3/report.html || echo "No report.html to copy"
# ls -larth $3/

# # Cleanup
# echo "End"
# docker rm -f ks_service_nest
# docker network rm test_db

#!/bin/bash

# Create Docker network
# docker network create test_db

# # Run the main service container with environment variables from the secret
# docker run -dit --name ks_service_nest --network test_db \
#   -e DATABASE_NAME=ks_dev_cluster_knowledgesearch_db_sql \
#   -e DATABASE_USERNAME=masterUsersql \
#   -e DATABASE_HOST=ks-db-dev.cvwkkmau6qnx.us-west-2.rds.amazonaws.com \
#   -e PYTHONPATH=/app \
#   -e DEBUG=True \
#   -e AUTH_KAAS_CLIENT_SECRET=byf9T3wXXcCljGKcPAWxs9sxow4EAA2J \
#   -e AUTH_DOCCEBO_PASSWORD=5w62992 \
#   -e AUTH_OPENSEARCH_PASSWORD=K3!0dg_7Hc \
#   -e AUTH_KZ_CLIENT_SECRET=aqfr1drih5k1ttdi6jq7oej9355ru37s \
#   -e AUTH_UID_CLIENT_SECRET=3euNa1Aty0tPN7d9mW1Y3BCFOAcHZbnTHNf1ifoMQmBHTztInM5mm03vkyp8C570 \
#   -e AUTH_API_SERIVCE_E2E_CLIENT_SECRET=gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v \
#   -w /app \
#   -e DATABASE_PORT=3306 \
#   -e DATABASE_PASSWORD=3cQHw1JbDdG4 \
#   -e DATABASE_SYNC=false \
#   -e DATABASE_LOGGING=true \
#   -e DATABASE_USE_CERT=false \
#   $2

# # Check if the container is running
# echo "Running container: $(docker ps -a)"
# sleep 30
# container_status=$(docker inspect -f '{{.State.Status}}' ks_service_nest)
# echo "Container status: $container_status"

# if [ "$container_status" != "running" ]; then
#     echo "Container is not running. Fetching logs for diagnosis..."
#     docker logs ks_service_nest
#     exit 1
# fi

# # Activate the virtual environment and execute test cases inside the running container
# echo "Executing test cases"
# docker exec -i ks_service_nest /bin/sh -c ". /opt/env/bin/activate && pytest" || { echo "Test execution failed"; exit 0; }
# #docker exec -i ks_service_nest /bin/sh -c "find / -name '*.html' 2>/dev/null" || echo "No report found"
# #docker exec -i ks_service_nest /bin/sh -c "mv /path/to/report.html /app/" || echo "Not able to copy the report"
# echo "PWD & Listing files"
# docker exec -i ks_service_nest pwd
# docker exec -i ks_service_nest ls -larth
# docker exec -i ks_service_nest /bin/sh -c "find / -name '*.html' -exec mv {} /app/ \;"

# # Output the current directory and list files in the container
# #echo "PWD & Listing files"
# #docker exec -i ks_service_nest pwd
# #docker exec -i ks_service_nest ls -larth

# # List files in the app directory
# #echo "PWD & Listing files in /app"
# #docker exec -i ks_service_nest ls -larth /app/
# #docker exec -i ks_service_nest ls -larth /app/apps
# #docker exec -i ks_service_nest ls -larth /ks_service_nest/app

# # Look for the report in the /app/apps directory
# #docker exec -i ks_service_nest ls -larth /app/apps
# #docker exec -i ks_service_nest cat /app/apps/report || echo "No report found"

# # Create output directory on the host
# #echo "Creating output directory"
# #mkdir -p $3/report/
# #ls -larth $3/

# # Copy the test report to the output directory (from /app/apps/report.html)
# echo "Copying the test report"
# docker exec -i ks_service_nest /bin/sh -c "echo 'Creating output directory'; mkdir -p /app/report/"
# docker exec -i ks_service_nest /bin/sh -c "ls -larth /app/"

# #docker cp ks_service_nest:/app/apps/report.html $3/report || echo "No report to copy"
# #ls -larth $3/

# # Cleanup
# echo "End"
# docker rm -f ks_service_nest
# docker network rm test_db


#!/bin/bash

# # Create Docker network
# docker network create test_db

# # Run the main service container with environment variables
# docker run -dit --name ks_service_nest --network test_db \
#   -e DATABASE_NAME=ks_dev_cluster_knowledgesearch_db_sql \
#   -e DATABASE_USERNAME=masterUsersql \
#   -e DATABASE_HOST=ks-db-dev.cvwkkmau6qnx.us-west-2.rds.amazonaws.com \
#   -e PYTHONPATH=/app \
#   -e DEBUG=True \
#   -e AUTH_KAAS_CLIENT_SECRET=byf9T3wXXcCljGKcPAWxs9sxow4EAA2J \
#   -e AUTH_DOCCEBO_PASSWORD=5w62992 \
#   -e AUTH_OPENSEARCH_PASSWORD=K3!0dg_7Hc \
#   -e AUTH_KZ_CLIENT_SECRET=aqfr1drih5k1ttdi6jq7oej9355ru37s \
#   -e AUTH_UID_CLIENT_SECRET=3euNa1Aty0tPN7d9mW1Y3BCFOAcHZbnTHNf1ifoMQmBHTztInM5mm03vkyp8C570 \
#   -e AUTH_API_SERIVCE_E2E_CLIENT_SECRET=gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v \
#   -w /app \
#   -e DATABASE_PORT=3306 \
#   -e DATABASE_PASSWORD=3cQHw1JbDdG4 \
#   -e DATABASE_SYNC=false \
#   -e DATABASE_LOGGING=true \
#   -e DATABASE_USE_CERT=false \
#   "$2"

# # Check if the container is running
# echo "Running container: $(docker ps -a)"
# sleep 30
# container_status=$(docker inspect -f '{{.State.Status}}' ks_service_nest)
# echo "Container status: $container_status"

# if [ "$container_status" != "running" ]; then
#     echo "Container is not running. Fetching logs for diagnosis..."
#     docker logs ks_service_nest
#     exit 1
# fi

# # Activate the virtual environment and execute test cases inside the running container
# echo "Executing test cases"
# docker exec -i ks_service_nest /bin/sh -c ". /opt/env/bin/activate && pytest" || { echo "Test execution failed"; exit 0; }

# # Move any generated reports to /app/report/
# echo "Searching for report files"
# docker exec -i ks_service_nest /bin/sh -c "find / -name '*.html' -exec mv {} /app/report/ \;"

# # Display contents of the report
# echo "Displaying report.html contents"
# docker exec -i ks_service_nest cat /app/report/report.html || echo "No report.html found"

# # Create output directory on the host
# echo "Creating output directory"
# mkdir -p "$3/report/"
# ls -larth "$3/"

# # Copy the test report to the output directory
# echo "Copying the test report"
# docker cp ks_service_nest:/app/report/report.html "$3/report.html" || echo "No report.html to copy"
# ls -larth "$3/"

# # Cleanup
# echo "Cleaning up..."
# docker rm -f ks_service_nest
# docker network rm test_db
# echo "End"


# Create Docker network
docker network create test_db

# Run the main service container with environment variables
docker run -dit --name ks_service_nest --network test_db \
  -e DATABASE_NAME=ks_dev_cluster_knowledgesearch_db_sql \
  -e DATABASE_USERNAME=masterUsersql \
  -e DATABASE_HOST=ks-db-dev.cvwkkmau6qnx.us-west-2.rds.amazonaws.com \
  -e PYTHONPATH=/app \
  -e DEBUG=True \
  -e AUTH_KAAS_CLIENT_SECRET=byf9T3wXXcCljGKcPAWxs9sxow4EAA2J \
  -e AUTH_DOCCEBO_PASSWORD=5w62992 \
  -e AUTH_OPENSEARCH_PASSWORD=K3!0dg_7Hc \
  -e AUTH_KZ_CLIENT_SECRET=aqfr1drih5k1ttdi6jq7oej9355ru37s \
  -e AUTH_UID_CLIENT_SECRET=3euNa1Aty0tPN7d9mW1Y3BCFOAcHZbnTHNf1ifoMQmBHTztInM5mm03vkyp8C570 \
  -e AUTH_API_SERIVCE_E2E_CLIENT_SECRET=gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v \
  -w /app \
  -e DATABASE_PORT=3306 \
  -e DATABASE_PASSWORD=3cQHw1JbDdG4 \
  -e DATABASE_SYNC=false \
  -e DATABASE_LOGGING=true \
  -e DATABASE_USE_CERT=false \
  "$2"

# Check if the container is running
echo "Running container: $(docker ps -a)"
sleep 30
container_status=$(docker inspect -f '{{.State.Status}}' ks_service_nest)
echo "Container status: $container_status"

if [ "$container_status" != "running" ]; then
    echo "Container is not running. Fetching logs for diagnosis..."
    docker logs ks_service_nest
    exit 1
fi

# Activate the virtual environment and execute test cases inside the running container
echo "Executing test cases"
docker exec -i ks_service_nest /bin/sh -c ". /opt/env/bin/activate && pytest" || { echo "Test execution failed"; exit 0; }

# Move any generated reports to /app/report/
echo "Searching for report files"
docker exec -i ks_service_nest /bin/sh -c "find / -name '*.html' -exec mv {} /app/report/ \;"

# Display contents of the report
echo "Displaying report.html contents"
docker exec -i ks_service_nest cat /app/report/report.html || echo "No report.html found"

# Create output directory on the host
echo "Creating output directory"
mkdir -p "$3/report/"
ls -larth "$3/"

# Copy the test report to the output directory
echo "Copying the test report"
docker cp ks_service_nest:/app/report/report.html "$3/report.html" || echo "No report.html to copy"
ls -larth "$3/"

# Send email with the test report
echo "Installing mailutils for email notification"
sudo apt-get install -y mailutils
if [ $? -ne 0 ]; then
    echo "Failed to install mailutils"
    exit 1
fi

echo "The test cases have been executed. Please find the reports attached." | mail -s "Test Cases Report" \
  -A "$3/report.html" neha.prasad@hp.com
if [ $? -ne 0 ]; then
    echo "Failed to send email"
    exit 1
fi

# Cleanup
echo "Cleaning up..."
docker rm -f ks_service_nest
docker network rm test_db
echo "End"
