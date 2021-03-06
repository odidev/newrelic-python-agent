# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from newrelic.api.external_trace import ExternalTrace
from newrelic.api.transaction import current_transaction
from newrelic.common.object_wrapper import wrap_function_wrapper


def bind_request(request, *args, **kwargs):
    return request


def sync_send_wrapper(wrapped, instance, args, kwargs):
    request = bind_request(*args, **kwargs)

    with ExternalTrace("httpx", str(request.url), request.method) as tracer:
        if hasattr(tracer, "generate_request_headers"):
            outgoing_headers = tracer.generate_request_headers(tracer.transaction)
            for header_name, header_value in outgoing_headers:
                # User headers should override our CAT headers
                if header_name not in request.headers:
                    request.headers[header_name] = header_value

        response = wrapped(*args, **kwargs)
        headers = dict(getattr(response, 'headers', None)).items()
        tracer.process_response(getattr(response, 'status_code', None), headers)

        return response


async def async_send_wrapper(wrapped, instance, args, kwargs):
    request = bind_request(*args, **kwargs)

    with ExternalTrace("httpx", str(request.url), request.method) as tracer:
        if hasattr(tracer, "generate_request_headers"):
            outgoing_headers = tracer.generate_request_headers(tracer.transaction)
            for header_name, header_value in outgoing_headers:
                # User headers should override our CAT headers
                if header_name not in request.headers:
                    request.headers[header_name] = header_value

        response = await wrapped(*args, **kwargs)
        headers = dict(getattr(response, 'headers', None)).items()
        tracer.process_response(getattr(response, 'status_code', None), headers)

        return response


def instrument_httpx_client(module):
    wrap_function_wrapper(module, "Client.send", sync_send_wrapper)
    wrap_function_wrapper(module, "AsyncClient.send", async_send_wrapper)
