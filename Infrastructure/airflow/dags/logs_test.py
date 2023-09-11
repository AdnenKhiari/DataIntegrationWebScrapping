from airflow import DAG
from docker.types import Mount
from airflow.providers.docker.operators.docker import DockerOperator
import datetime
from airflow.operators.bash import BashOperator
from airflow.models import Connection

run_id  = "{{run_id}}"

def get_lib_mount():
    return Mount(source="/home/adnen/Documents/Stage Wimbee/jobs/talend_output/Job Designs/lib",target="/app/lib",type="bind")

shared_args = {
    "tls_hostname":False,
    "mount_tmp_dir":False,
    "docker_conn_id":"docker_pv_registry",
    "auto_remove":True
}


def get_talend_job(name,custom_mounts=None,version="1.0"):

    if custom_mounts == None:
        custom_mounts = []
    return DockerOperator(
            task_id=name,
            image=f"localhost:5000/{name}:{version}",
            mounts = [
                *custom_mounts,
                get_lib_mount()     
            ],
            container_name=name,
            **shared_args,
            environment={"RUN_ID": run_id,"PROM_GATEWAY_ENV_CONN":"172.17.0.1:9091" }    
        )


with DAG(
    dag_id="jlogs",
    description="ETL to scap job offers Stage",
    default_args={
        'owner': "AdnenKh"
    },
    start_date=datetime.datetime.now(),
    schedule="@weekly"
    ) as dag:

    ods_conn = Connection.get_connection_from_secrets("ods_db_connection")

    hello_work_scrap_data = DockerOperator(
        task_id="hello_work_scrap_data",
        image="localhost:5000/hello_work_scrap:1.0",
        container_name="hello_work_scrap_data",
        mounts=[Mount(source="/home/adnen/Documents/Stage Wimbee/datasets/hello_work",target="/app/output_hello_work",type="bind")],
        command="python HelloWork/main.py --keywords=azure --ds={{prev_execution_date_success}} --thread-num=2",
        **shared_args,
        port_bindings={9777:9777},
        environment={"HUB_HOSTNAME":"172.17.0.1","RUN_ID": run_id}
    )
    hello_work_scrap_data
    
