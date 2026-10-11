"""Disposable-only wire model; never production feasibility or runtime behavior."""
from contextlib import closing
import re
import sys
from time import monotonic,sleep

from psycopg import Cursor

RTT_SECONDS = 0.029993
PAYLOAD_BYTES_PER_SECOND = 12000000
TOTAL_STREAM_BYTES = 379493362
TABLE_BYTES = {'education79_transport_context':256831749,'education79_transport_votes':104017692}


def table_scales(timings):
    others=sum(t['utf8_bytes'] for t in timings if t['table'] not in TABLE_BYTES)
    return {t['table']:(TABLE_BYTES[t['table']]/t['utf8_bytes'] if t['table'] in TABLE_BYTES
                       else (TOTAL_STREAM_BYTES-sum(TABLE_BYTES.values()))/others) for t in timings}


def model_cursor(scales,metrics):
    class WireCursor(Cursor):
        def execute(self,*args,**kwargs):
            sleep(RTT_SECONDS)
            return super().execute(*args,**kwargs)

        def stream(self,statement,params=None,*,size=1,**kwargs):
            assert size==1  # Compatible single-row protocol, no chunked API use.
            table=re.search(r'FROM "([^"]+)" t',statement.as_string()).group(1)
            sleep(RTT_SECONDS);wire_started=None;wire_bytes=0.0;count=0
            # Match a continuous flow; CPU work may overlap arrival. No per-row RTT.
            with closing(super().stream(statement,params,size=1,**kwargs)) as rows:
                for row in rows:
                    if wire_started is None:wire_started=monotonic()
                    count+=1;raw=len(row['row_text'].encode('utf-8'))+1
                    wire_bytes+=raw*scales[table]
                    metrics['modeled_bytes']+=raw*scales[table]
                    metrics['largest_decoded_object_bytes_estimate']=max(metrics['largest_decoded_object_bytes_estimate'],
                        sys.getsizeof(row)+sum(sys.getsizeof(k)+sys.getsizeof(v) for k,v in row.items()))
                    if count%4096==0:
                        delay=max(0,wire_bytes/PAYLOAD_BYTES_PER_SECOND-(monotonic()-wire_started))
                        if delay:sleep(delay)
                    yield row
                if wire_started is not None:
                    delay=max(0,wire_bytes/PAYLOAD_BYTES_PER_SECOND-(monotonic()-wire_started))
                    if delay:sleep(delay)
    return WireCursor
