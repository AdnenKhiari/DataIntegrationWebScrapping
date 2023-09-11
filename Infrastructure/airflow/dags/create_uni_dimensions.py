from airflow import DAG
from docker.types import Mount
from airflow.providers.docker.operators.docker import DockerOperator
import datetime
from airflow.operators.bash import BashOperator

run_id  = "{{run_id}}"

def get_lib_mount():
    return Mount(source="/home/adnen/Documents/Stage Wimbee/jobs/talend_output/Job Designs/lib",target="/app/lib",type="bind")

shared_args = {
    "tls_hostname":False,
    "mount_tmp_dir":False,
    "docker_conn_id":"docker_pv_registry",
    "auto_remove":True,
    "environment":{"RUN_ID": run_id,"PROM_GATEWAY_ENV_CONN":"172.17.0.1:9091" }    
}

with DAG(
    dag_id="dw_date_dim",
    description="load the date dim",
    default_args={
        'owner': "AdnenKh"
    },
    start_date=datetime.datetime.now(),
    schedule="@once"
    ) as dag:
    dw_date_dim = DockerOperator(
        task_id="dw_date_dim_task",
        image="localhost:5000/dw_date_dim:1.0",
        mounts = [
            get_lib_mount()      
        ],
        container_name="dw_date_dim",
        **shared_args
    )
    dw_date_dim 
