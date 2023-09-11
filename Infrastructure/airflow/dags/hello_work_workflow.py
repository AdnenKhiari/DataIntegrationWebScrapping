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
    dag_id="Job_Scrapping_DW_v1.0",
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
    get_skills_from_jobs = DockerOperator(
        task_id="get_skills_from_jobs",
        image="localhost:5000/skill_extractor:1.0",
        container_name="get_skills_from_jobs",
        port_bindings={9987:9987},
        environment={"DB_HOST":ods_conn.host,"DB_PASSWORD":ods_conn.password},
        **shared_args  
    )
    company_details_scrap = DockerOperator(
        task_id="company_details_scrap",
        image="localhost:5000/company_details_scrap:1.0",
        container_name="company_details_scrap",
        **shared_args,
        port_bindings={9777:9988},
        command="python main.py --thread-num=1",
        environment={"DB_HOST":ods_conn.host,"HUB_HOSTNAME":"172.17.0.1","RUN_ID": run_id,"DB_PASSWORD":ods_conn}
    )
    ods_hw_load_data = get_talend_job("ods_hw_load_data",[Mount(source="/home/adnen/Documents/Stage Wimbee/datasets/hello_work",target="/datasets/hello_work",type="bind")   ])
    ods_hw_preprocess_data = get_talend_job("ods_hw_preprocess_data")
    dw_hw_company_dim = get_talend_job("dw_hw_company_dim")
    dw_hw_contract_regime_dim = get_talend_job("dw_hw_contract_regime_dim")
    dw_hw_contract_teletravail_dim = get_talend_job("dw_hw_contract_teletravail_dim")
    dw_hw_contract_type_dim = get_talend_job("dw_hw_contract_type_dim")
    dw_hw_job_dim = get_talend_job("dw_hw_job_dim")
    dw_hw_localisation_dim = get_talend_job("dw_hw_localisation_dim")

    dw_hw_skills_dim = get_talend_job("dw_hw_skills_dim")

    dw_hw_job_offer_fact = get_talend_job("dw_hw_job_offer_fact")
    dw_hw_job_skills_fact = get_talend_job("dw_hw_job_skills_fact")
    dw_company_financial_fact = get_talend_job("dw_company_financial_fact")

    dims = [
        dw_hw_company_dim,
        dw_hw_contract_regime_dim,
        dw_hw_contract_teletravail_dim,
        dw_hw_contract_type_dim,
        dw_hw_job_dim,
        dw_hw_localisation_dim
    ]

    hello_work_scrap_data >> ods_hw_load_data >> ods_hw_preprocess_data >> dims

    for dim in dims:
        dim >> dw_hw_job_offer_fact


    [ods_hw_load_data >> get_skills_from_jobs >> dw_hw_skills_dim,dw_hw_job_dim,dw_hw_company_dim] >> dw_hw_job_skills_fact

    ods_hw_preprocess_data   >> company_details_scrap >> dw_hw_company_dim >> dw_company_financial_fact
