import json
import os
import boto3
import urllib3

ecs_client = boto3.client('ecs')

SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
http = urllib3.PoolManager()

def get_log_group_name(task_def_arn):
    task_definition = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    log_group = task_definition['taskDefinition']['containerDefinitions'][0]['logConfiguration']['options'].get('awslogs-group')
    if not log_group:
        raise Exception(f"No log group found for the task definition: {task_def_arn}")
    return log_group

def lambda_handler(event, context):
    # Extract ECS event details
    cluster_name = event['detail']['clusterArn']
    task_arn = event['detail']['taskArn']
    task_status = event['detail']['lastStatus']

    ecs_event = event['detail']
    last_status = ecs_event.get('lastStatus', 'N/A')

    cluster_name = ecs_event.get('clusterArn', '').split('/')[-1]
    service_name = ecs_event.get('group', '').split(':')[-1]
    task_arn = ecs_event.get('taskArn', 'N/A')
    task_definition_arn = ecs_event.get('taskDefinitionArn', 'N/A')
    docker_image = ecs_event['containers'][0].get('image', 'N/A')
    container_name = ecs_event['containers'][0].get('name', 'N/A')

    log_group_name = get_log_group_name(task_definition_arn)
    task_id = task_arn.split('/')[-1]
    environment = cluster_name.split('-')[-1]
    log_stream_name = f"{environment}/{container_name}/{task_id}"

    message = {
        "text": f"ECS Task State Change Notification\n"
                f"Cluster: {cluster_name}\n"
                f"Task ID: {task_id}\n"
                f"Last State: {task_status}\n"
                f"Time: {event['time']}\n"
                f"Service Name: {service_name}\n"
                f"Docker Image: {docker_image}\n"
                f"Container Name: {container_name}\n"
                f"Task Definition ARN: {task_definition_arn}\n"
                f"Log Group Name: {log_group_name}\n"
                f"Log Stream Name: {log_stream_name}\n"
                f"Environment: {environment}"
    }

    try:
        # Send the notification to Slack using urllib3
        encoded_message = json.dumps(message).encode('utf-8')
        response = http.request(
            'POST',
            SLACK_WEBHOOK_URL,
            body=encoded_message,
            headers={'Content-Type': 'application/json'}
        )

        # Check for a successful response
        if response.status == 200:
            try:
                # Try to parse the response as JSON (though it may be empty)
                print(json.loads(response.data.decode('utf-8')))  # Log the JSON response
            except ValueError:
                print(f"Non-JSON response from Slack: {response.data.decode('utf-8')}")
        else:
            print(f"Error sending Slack notification. HTTP status: {response.status}")

    except urllib3.exceptions.HTTPError as e:
        print(f"Error sending Slack notification: {e}")
        # Log the response status code to investigate further
        print(f"Slack response status code: {response.status}")
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Notification sent successfully!')
    }
