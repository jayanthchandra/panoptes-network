from os import getenv
import flask

import psycopg2.extensions
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError

CONNECTION_NAME = getenv(
    'INSTANCE_CONNECTION_NAME',
    'panoptes-survey:us-central1:panoptes-meta'
)
DB_USER = getenv('POSTGRES_USER', 'panoptes')
DB_PASSWORD = getenv('POSTGRES_PASSWORD', None)
DB_NAME = getenv('POSTGRES_DATABASE', 'metadata')
pg_config = {
    'user': DB_USER,
    'password': DB_PASSWORD,
    'dbname': DB_NAME
}

# Give back floats instead of Decimal so we don't have to bother with serializer.
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)

# Connection pools reuse connections between invocations,
# and handle dropped or expired connections automatically.
pg_pool = None


def __connect(host):
    """
    Helper function to connect to Postgres
    """
    global pg_pool
    pg_config['host'] = host
    pg_pool = SimpleConnectionPool(1, 1, **pg_config)


def get_observations(sequence_id=None):
    global pg_pool

    # Initialize the pool lazily, in case SQL access isn't needed for this
    # GCF instance. Doing so minimizes the number of active SQL connections,
    # which helps keep your GCF instances under SQL connection limits.
    if not pg_pool:
        try:
            __connect('/cloudsql/{}'.format(CONNECTION_NAME))
        except OperationalError as e:
            print(e)
            # If production settings fail, use local development ones
            __connect('localhost')
    conn = pg_pool.getconn()
    conn.set_isolation_level(0)

    if sequence_id:
        select_sql = """
            SELECT *
            FROM sequences t1, images t2
            WHERE t1.id=t2.sequence_id
                AND t1.id=%s
            ORDER BY t2.date_obs DESC
            """
    else:
        select_sql = """
            SELECT t1.*, count(t2.id) as image_count
            FROM sequences t1, images t2
            WHERE t1.id=t2.sequence_id
            GROUP BY t1.id
            ORDER BY t1.start_date DESC
            """

    rows = list()
    with conn.cursor() as cursor:
        cursor.execute(select_sql, (sequence_id, ))
        rows = cursor.fetchall()
        cursor.close()

    pg_pool.putconn(conn)

    return rows


def get_observations_data(request):
    request_json = request.get_json()

    sequence_id = None
    if request_json and 'sequence_id' in request_json:
        sequence_id = request_json['sequence_id']

    rows = get_observations(sequence_id)

    return flask.jsonify(dict(data=rows, count=len(rows)))