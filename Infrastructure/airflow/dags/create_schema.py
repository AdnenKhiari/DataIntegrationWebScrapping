from airflow import DAG
from docker.types import Mount
from airflow.providers.docker.operators.docker import DockerOperator
import datetime
from airflow.operators.bash import BashOperator
from airflow.models import Connection

run_id  = "{{run_id}}"

def get_sqlcmd(task_id,filepath,cname):
    db_conn = Connection.get_connection_from_secrets("ods_db_connection"	)
    return DockerOperator(
        task_id=task_id,
        tls_hostname=False,
        image="localhost:5000/sqlcmd:1.0",
        mounts = [
            Mount(source="/home/adnen/Documents/Stage Wimbee/jobs/sql_jobs/sql",target="/sql",type="bind")        
        ],
        command=f"sqlcmd -S {db_conn.host},{db_conn.port} -U {db_conn.login} -P {db_conn.password}! -N -C -i "+filepath+" -b",
        docker_conn_id="docker_pv_registry",
        container_name=cname,
        auto_remove=True
        )

with DAG(
    dag_id="create_schema",
    description="create the ods and datawarehouse schemas",
    default_args={
        'owner': "AdnenKh"
    },
    start_date=datetime.datetime.now(),
    schedule="@once"
    ) as dag:
    
    create_ods_tables = get_sqlcmd("create_ods_tables","/sql/ods.sql","create_ods_tables")
    create_dw_tables = get_sqlcmd("create_dw_tables","/sql/dw.sql","create_dw_tables")

    
    bs = BashOperator(
        task_id="test_bash",
        bash_command="echo 'hiii "+ run_id +"' "
        )

    create_ods_tables >> bs
    create_dw_tables >> bs



