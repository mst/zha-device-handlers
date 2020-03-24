from zigpy.profiles import PROFILES, zha
from zigpy.zcl.clusters.general import Basic, Identify,\
    Ota, PowerConfiguration, Time, Groups
from zigpy.zcl.clusters.hvac import Thermostat
from zigpy.quirks import CustomDevice, CustomCluster
import zigpy.types as types
from zigpy.zcl import foundation

THERMOSTAT_CHANNEL = 'thermostat'

class SpiritZigbee(CustomDevice):
    """Custom device representing Eurotronic Spirit Zigbee thermostats"""

    class ThermostatCluster(CustomCluster, Thermostat):
        """Eurotronic Spirit Zigbee thermostat cluster"""

        cluster_id = Thermostat.cluster_id

        MANUFACTURER                    = 0x1037

        OCCUPIED_HEATING_SETPOINT_ATTR  = 0x0012
        CTRL_SEQ_OF_OPER_ATTR           = 0x001B
        SYSTEM_MODE_ATTR                = 0x001C

        TRV_MODE_ATTR                   = 0x4000
        SET_VALVE_POS_ATTR              = 0x4001
        ERRORS_ATTR                     = 0x4002
        CURRENT_TEMP_SETPOINT_ATTR      = 0x4003
        HOST_FLAGS_ATTR                 = 0x4008

        SET_OFF_MODE_FLAG               = 0x000020
        CLR_OFF_MODE_FLAG               = 0x000010
        OFF_MODE_MASK                   = 0x000010

        def __init__(self, *args, **kwargs):
            """Init."""
            super().__init__(*args, **kwargs)

            self.attributes.update({
                self.TRV_MODE_ATTR:              ('trv_mode', types.enum8),
                self.SET_VALVE_POS_ATTR:         ('set_valve_position', types.uint8_t),
                self.ERRORS_ATTR:                ('errors', types.uint8_t),
                self.CURRENT_TEMP_SETPOINT_ATTR: ('current_temperature_setpoint', types.int16s),
                self.HOST_FLAGS_ATTR:            ('host_flags', types.uint24_t),
            })
            self._attridx = {
                attrname: attrid for attrid, (attrname, datatype)
                in self.attributes.items()
            }
            super().write_attributes({'ctrl_seqe_of_oper': 0x02})

        def _update_attribute(self, attrid, value):
            if attrid == self.OCCUPIED_HEATING_SETPOINT_ATTR:
                return
            elif attrid == self.CURRENT_TEMP_SETPOINT_ATTR:
                super()._update_attribute(self.OCCUPIED_HEATING_SETPOINT_ATTR, value)
            elif attrid == self.CTRL_SEQ_OF_OPER_ATTR:
                super()._update_attribute(self.CTRL_SEQ_OF_OPER_ATTR, 0x02)
                return
            elif attrid == self.HOST_FLAGS_ATTR:
                if value & self.OFF_MODE_MASK == self.OFF_MODE_MASK:
                    super()._update_attribute(self.SYSTEM_MODE_ATTR, 0x0)
                else:
                    super()._update_attribute(self.SYSTEM_MODE_ATTR, 0x4)
            super()._update_attribute(attrid, value)

        def write_attributes(self, attributes, is_report=False, manufacturer=None):
            if 'system_mode' in attributes and is_report == False:
                if attributes.get('system_mode') == 0x0:
                    host_flags = self._attr_cache[self.HOST_FLAGS_ATTR] | self.SET_OFF_MODE_FLAG
                    return super().write_attributes({'host_flags': host_flags}, False, self.MANUFACTURER)
                elif attributes.get('system_mode') == 0x4:
                    host_flags = self._attr_cache[self.HOST_FLAGS_ATTR] | self.CLR_OFF_MODE_FLAG
                    return super().write_attributes({'host_flags': host_flags}, False, self.MANUFACTURER)

            return super().write_attributes(attributes, is_report, manufacturer)

    signature = {
        # <SimpleDescriptor endpoint=1 profile=260 device_type=769
        # device_version=1
        # input_clusters=[0, 1, 3, 513, 25, 10]
        # output_clusters=[0, 1, 3, 4, 513, 25, 10]>
        1: {
            'manufacturer': 'Eurotronic',
            'model': 'SPZB0001',
            'profile_id': zha.PROFILE_ID,
            'device_type': zha.DeviceType.THERMOSTAT,
            'input_clusters': [
                Basic.cluster_id,
                PowerConfiguration.cluster_id,
                Identify.cluster_id,
                Thermostat.cluster_id,
                Ota.cluster_id,
                Time.cluster_id,
            ],
            'output_clusters': [
                Basic.cluster_id,
                PowerConfiguration.cluster_id,
                Identify.cluster_id,
                Groups.cluster_id,
                Thermostat.cluster_id,
                Ota.cluster_id,
                Time.cluster_id,
            ],
        }
    }

    replacement = {
        'endpoints': {
            1: {
                'manufacturer': 'Eurotronic',
                'model': 'SPZB0001',
                'profile_id': zha.PROFILE_ID,
                'device_type': zha.DeviceType.THERMOSTAT,
                'input_clusters': [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    ThermostatCluster,
                    Ota.cluster_id,
                    Time.cluster_id,
                ],
                'output_clusters': [
                    Basic.cluster_id,
                    PowerConfiguration.cluster_id,
                    Identify.cluster_id,
                    Groups.cluster_id,
                    ThermostatCluster,
                    Ota.cluster_id,
                    Time.cluster_id,
                ],
            }
        }
    }
