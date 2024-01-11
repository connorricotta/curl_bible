import logging
import time
from traceback import format_exception

import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class InfluxDBSettings(BaseSettings):
    INFLUXDB_TOKEN: str
    INFLUXDB_ORG: str
    INFLUXDB_URL: str
    INFLUXDB_BUCKET: str
    model_config = ConfigDict(extra="ignore")
    # SettingsConfigDict(env_file=".env")


class InfluxDBWriter:
    def __init__(self):
        self.settings = InfluxDBSettings()
        self.writer = influxdb_client.InfluxDBClient(
            url=self.settings.INFLUXDB_URL,
            token=self.settings.INFLUXDB_TOKEN,
            org=self.settings.INFLUXDB_ORG,
        )
        self.writer_cursor = self.writer.write_api(write_options=SYNCHRONOUS)
        self.bucket = self.settings.INFLUXDB_BUCKET

    def log(self, value):
        data = (
            Point("log")
            .tag("filename", value.filename)
            .tag("function_name", value.funcName)
            .tag("message", value.msg)
            .tag("line_number", value.lineno)
            .field("level", value.levelno)
        )
        if isinstance(value.msg, Exception):
            for count, traceback_level in enumerate(format_exception(value.msg)):
                data.tag(f"traceback_level_{count:02}", traceback_level)

        self.writer_cursor.write(
            bucket=self.bucket, org=self.settings.INFLUXDB_ORG, record=data
        )


class InfluxDBHTTPHandler(logging.Handler):
    def __init__(self):
        self.rest = InfluxDBWriter()
        super().__init__()

    def emit(self, record):
        self.rest.log(record)


if __name__ == "__main__":
    test = InfluxDBWriter()
    # test.log("Thing")

    # token = os.environ.get("INFLUXDB_TOKEN")
    # org = "CheeseINC"
    # url = "http://192.168.0.2:8086"

    influxdb_settings = InfluxDBSettings()
    # Writing to InfluxDB
    write_client = influxdb_client.InfluxDBClient(
        url=influxdb_settings.INFLUXDB_URL,
        token=influxdb_settings.INFLUXDB_TOKEN,
        org=influxdb_settings.INFLUXDB_ORG,
    )

    bucket = influxdb_settings.INFLUXDB_BUCKET

    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    for write_value in range(5):
        point = (
            Point("measurement1")
            .tag("tagname1", "tagvalue1")
            .field("field1", write_value)
        )
        write_api.write(bucket=bucket, org=influxdb_settings.INFLUXDB_ORG, record=point)
        time.sleep(1)  # separate points by 1 second

    # Simple Query
    query_api = write_client.query_api()

    QUERY = """from(bucket: "curl_bible")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "measurement1")"""
    tables = query_api.query(QUERY, org=influxdb_settings.INFLUXDB_ORG)

    for table in tables:
        for table_record in table.records:
            print(table_record)

    # Complex Query
    query_api = write_client.query_api()

    QUERY2 = """from(bucket: "curl_bible")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "measurement1")
    |> mean()"""
    tables = query_api.query(QUERY2, org=influxdb_settings.INFLUXDB_ORG)

    for table in tables:
        for table_record in table.records:
            print(table_record)
