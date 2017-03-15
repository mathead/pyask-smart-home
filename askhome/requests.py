from datetime import datetime

from .utils import rstrip_word


def create_request(data, context=None):
    name = data['header']['name']

    # Return Request subtype for specific requests
    if name == 'DiscoverAppliancesRequest':
        return DiscoverRequest(data, context)

    if name in ('IncrementPercentageRequest',
                'DecrementPercentageRequest',
                'SetPercentageRequest'):
        return PercentageRequest(data, context)

    if name in ('IncrementTargetTemperatureRequest',
                'DecrementTargetTemperatureRequest',
                'SetTargetTemperatureRequest'):
        return ChangeTemperatureRequest(data, context)

    if name == 'GetTargetTemperatureRequest':
        return GetTemperatureRequest(data, context)

    if name == 'GetTemperatureReadingRequest':
        return TemperatureReadingRequest(data, context)

    if name in ('SetLockStateRequest', 'GetLockStateRequest'):
        return LockStateRequest(data, context)

    if name == 'HealthCheckRequest':
        return HealthCheckRequest(data, context)

    return Request(data, context)


class Request(object):
    def __init__(self, data, context=None):
        self.data = data
        self.context = context

        self.header = data['header']
        self.payload = data['payload']
        self.name = self.header['name']
        self.access_token = self.payload.get('accessToken', None)

    @property
    def appliance_id(self):
        if 'appliance' not in self.payload:
            return None
        return self.payload['appliance']['applianceId']

    @property
    def appliance_details(self):
        if 'appliance' not in self.payload:
            return None
        return self.payload['appliance']['additionalApplianceDetails']

    def response_header(self, name=None):
        if name is None:
            # Figure out response name - Control requests have confirmations instead of responses
            name = rstrip_word(self.name, 'Request')
            if self.header['namespace'] == 'Alexa.ConnectedHome.Control':
                name += 'Confirmation'
            else:
                name += 'Response'

        # Copy request header and just change the name
        header = dict(self.header)
        header['name'] = name

        return header

    def raw_response(self, payload=None, header=None):
        if payload is None:
            payload = {}
        if header is None:
            header = self.response_header()

        return {'header': header, 'payload': payload}

    def response(self, *args, **kwargs):
        return self.raw_response()

    def exception_response(self, exception):
        # Use exception class name as response name
        header = self.response_header(exception.name)
        header['namespace'] = exception.namespace

        return {'header': header, 'payload': exception.payload}

    @staticmethod
    def _format_timestamp(timestamp):
        if isinstance(timestamp, datetime):
            # Format datetime according to documentation
            return timestamp.replace(microsecond=0).isoformat()
        else:
            return timestamp


class DiscoverRequest(Request):
    def response(self, smarthome):
        discovered = []
        for appl_id, (appl, details) in smarthome.appliances.iteritems():
            # Helper function to get detail in hierarchy:
            # Smarthome.add_device kwargs -> Appliance.Details -> Smarthome.__init__ kwargs
            def get_detail(name, default=''):
                if name in details:
                    return details[name]
                if hasattr(appl, 'Details') and hasattr(appl.Details, name):
                    return getattr(appl.Details, name)
                return smarthome.details.get(name, default)

            serialized = {
                'applianceId': appl_id,
                'manufacturerName': get_detail('manufacturer'),
                'modelName': get_detail('model'),
                'version': get_detail('version'),
                'friendlyName': get_detail('name'),
                'friendlyDescription': get_detail('description'),
                'isReachable': get_detail('reachable', True),
                'additionalApplianceDetails': get_detail('additional_details', {}),
                'actions': sorted(appl.actions.keys()),  # sorted for easier testing
            }
            discovered.append(serialized)

        return self.raw_response({'discoveredAppliances': discovered})


class PercentageRequest(Request):
    @property
    def percentage(self):
        if 'percentageState' not in self.payload:
            return None
        return self.payload['percentageState']['value']

    @property
    def delta_percentage(self):
        if 'deltaPercentage' not in self.payload:
            return None
        return self.payload['deltaPercentage']['value']


class TemperatureRequest(Request):
    @property
    def temperature(self):
        if 'targetTemperature' not in self.payload:
            return None
        return self.payload['targetTemperature']['value']

    @property
    def delta_temperature(self):
        if 'deltaTemperature' not in self.payload:
            return None
        return self.payload['deltaTemperature']['value']


class ChangeTemperatureRequest(TemperatureRequest):
    def response(self, temperature, mode='AUTO', previous_temperature=None, previous_mode='AUTO'):
        payload = {
            'targetTemperature': {
                "value": temperature
            },
            'temperatureMode': {
                'value': mode
            }
        }

        # Even though the docs say the previousState is required, it works fine without it
        if previous_temperature is not None:
            payload['previousState'] = {
                'targetTemperature': {
                    'value': previous_temperature
                },
                'mode': {
                    'value': previous_mode
                }
            }

        return self.raw_response(payload)


class GetTemperatureRequest(TemperatureRequest):
    def response(self, temperature=None, cooling_temperature=None, heating_temperature=None,
                 mode='AUTO', mode_name=None, timestamp=None):
        payload = {
            'temperatureMode': {'value': mode}
        }

        if temperature is not None:
            payload['targetTemperature'] = {'value': temperature}
        if cooling_temperature is not None:
            payload['coolingTargetTemperature'] = {'value': cooling_temperature}
        if heating_temperature is not None:
            payload['heatingTargetTemperature'] = {'value': heating_temperature}
        if mode_name is not None:
            payload['temperatureMode']['friendlyName'] = mode_name
        # Add timestamp to payload if set
        if timestamp is not None:
            payload['applianceResponseTimestamp'] = self._format_timestamp(timestamp)

        return self.raw_response(payload)


class TemperatureReadingRequest(TemperatureRequest):
    def response(self, temperature, timestamp=None):
        payload = {'temperatureReading': {'value': temperature}}
        # Add timestamp to payload if set
        if timestamp is not None:
            payload['applianceResponseTimestamp'] = self._format_timestamp(timestamp)
        return self.raw_response(payload)


class LockStateRequest(Request):
    @property
    def lock_state(self):
        return self.payload['lockState']

    def response(self, lock_state, timestamp=None):
        payload = {'lockState': lock_state}
        # Add timestamp to payload if set
        if timestamp is not None:
            payload['applianceResponseTimestamp'] = self._format_timestamp(timestamp)
        return self.raw_response(payload)


class HealthCheckRequest(Request):
    def response(self, healthy, description):
        return self.raw_response({
            'isHealthy': healthy,
            'description': description
        })