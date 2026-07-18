"""
obd_reader.py
--------------
Módulo responsável por conectar no adaptador ELM327 (Bluetooth) e ler os
dados reais do veículo via protocolo OBD-II.

Funciona 100% local — nenhuma informação do carro passa pela internet.

IMPORTANTE SOBRE OS LIMITES DO ELM327 COMUM:
Este módulo lê os PIDs PADRÃO do protocolo OBD-II (definidos pela SAE),
que qualquer scanner ELM327 consegue acessar. Sistemas proprietários da
PSA/Citroën (suspensão Hydractive, módulo de conforto BSI, temperatura
do óleo do câmbio AL4/AM6) usam protocolos de diagnóstico específicos do
fabricante que um ELM327 genérico NÃO consegue ler — isso exigiria uma
ferramenta de diagnóstico própria da marca (tipo Lexia/Diagbox/PP2000).

COMO O BLUETOOTH APARECE NO PC:
No Windows, depois de parear o ELM327 nas configurações de Bluetooth do
Windows, ele cria uma porta COM virtual (ex: COM5, COM7...). É essa porta
que usamos aqui embaixo.

No Linux, geralmente aparece como /dev/rfcomm0 (às vezes é preciso rodar
`sudo rfcomm bind 0 <MAC_DO_ELM327>` antes).

Se não encontrar o adaptador, o modo DEMO entra em ação sozinho, gerando
valores simulados — assim dá pra testar a interface sem estar no carro.
"""

import random
import time
import threading
import logging

logger = logging.getLogger("c5.obd")

try:
    import obd
    OBD_LIB_AVAILABLE = True
except ImportError:
    OBD_LIB_AVAILABLE = False
    logger.warning("Biblioteca python-obd não instalada. Rode: pip install -r requirements.txt")


class OBDReader:
    def __init__(self, portstr: str = None, demo_mode: bool = False):
        """
        portstr: porta COM (Windows, ex: 'COM5') ou /dev/rfcomm0 (Linux).
                 Se deixar None, o python-obd tenta auto-detectar.
        demo_mode: força modo simulado (útil para testar sem o carro).
        """
        self.portstr = portstr
        self.demo_mode = demo_mode or not OBD_LIB_AVAILABLE
        self.connection = None
        self._lock = threading.Lock()
        self._demo_state = {"rpm": 800, "speed": 0, "throttle": 3}

        if not self.demo_mode:
            self._connect()

    def _connect(self):
        try:
            logger.info(f"Conectando no ELM327 ({self.portstr or 'auto-detect'})...")
            self.connection = obd.OBD(self.portstr) if self.portstr else obd.OBD()
            if not self.connection.is_connected():
                logger.warning("Não foi possível conectar ao ELM327. Entrando em modo DEMO.")
                self.demo_mode = True
            else:
                logger.info("Conectado ao ELM327 com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao conectar no OBD2: {e}")
            self.demo_mode = True

    def is_connected(self) -> bool:
        if self.demo_mode:
            return False
        return self.connection is not None and self.connection.is_connected()

    def _query(self, command_name: str):
        """Faz uma leitura segura de um PID do OBD2."""
        if self.demo_mode or self.connection is None:
            return None
        try:
            cmd = getattr(obd.commands, command_name)
            response = self.connection.query(cmd)
            if response.is_null():
                return None
            return response.value
        except Exception as e:
            logger.error(f"Erro ao ler {command_name}: {e}")
            return None

    def get_snapshot(self) -> dict:
        """
        Retorna um dicionário com os dados atuais do veículo. Além dos
        básicos (RPM, velocidade, temperatura, combustível, acelerador,
        bateria), agora também traz: carga do motor, temperatura do ar
        de admissão, fluxo de ar (MAF), sondas lambda, trim de
        combustível, e códigos de falha (DTC) — tudo PID padrão OBD2,
        lido de verdade de um ELM327 comum.
        """
        if self.demo_mode:
            return self._demo_snapshot()

        rpm = self._query("RPM")
        speed = self._query("SPEED")
        coolant_temp = self._query("COOLANT_TEMP")
        fuel_level = self._query("FUEL_LEVEL")
        throttle = self._query("THROTTLE_POS")
        voltage = self._query("CONTROL_MODULE_VOLTAGE")
        intake_temp = self._query("INTAKE_TEMP")
        engine_load = self._query("ENGINE_LOAD")
        maf = self._query("MAF")
        o2_b1s1 = self._query("O2_B1S1")
        fuel_trim_short = self._query("SHORT_FUEL_TRIM_1")
        fuel_trim_long = self._query("LONG_FUEL_TRIM_1")
        dtc_list, mil_on = self._query_dtc()

        return {
            "connected": True,
            "rpm": round(rpm.magnitude) if rpm else None,
            "speed_kmh": round(speed.magnitude) if speed else None,
            "engine_temp_c": round(coolant_temp.magnitude) if coolant_temp else None,
            "fuel_percent": round(fuel_level.magnitude) if fuel_level else None,
            "throttle_percent": round(throttle.magnitude) if throttle else None,
            "battery_v": round(voltage.magnitude, 1) if voltage else None,
            "intake_temp_c": round(intake_temp.magnitude) if intake_temp else None,
            "engine_load_percent": round(engine_load.magnitude) if engine_load else None,
            "maf_gs": round(maf.magnitude, 1) if maf else None,
            "o2_voltage_v": round(o2_b1s1.magnitude, 2) if o2_b1s1 else None,
            "fuel_trim_short_percent": round(fuel_trim_short.magnitude, 1) if fuel_trim_short else None,
            "fuel_trim_long_percent": round(fuel_trim_long.magnitude, 1) if fuel_trim_long else None,
            "dtc_codes": dtc_list,
            "mil_on": mil_on,
            "timestamp": time.time(),
        }

    def _query_dtc(self):
        """
        Lê os códigos de falha ativos (DTC) e o status da luz de injeção
        (MIL - Malfunction Indicator Lamp). Retorna (lista_de_codigos, mil_ligada).
        """
        if self.demo_mode or self.connection is None:
            return [], False
        try:
            response = self.connection.query(obd.commands.GET_DTC)
            if response.is_null() or not response.value:
                status = self.connection.query(obd.commands.STATUS)
                mil_on = bool(status.value.MIL) if not status.is_null() else False
                return [], mil_on
            codes = [f"{code} - {desc}" for code, desc in response.value]
            return codes, True
        except Exception as e:
            logger.error(f"Erro ao ler DTCs: {e}")
            return [], False

    def _demo_snapshot(self) -> dict:
        """Gera valores simulados e realistas, para testar sem o carro."""
        s = self._demo_state
        s["rpm"] = max(750, min(3000, s["rpm"] + random.randint(-30, 30)))
        s["speed"] = max(0, min(120, s["speed"] + random.randint(-2, 3)))
        s["throttle"] = max(0, min(100, s["throttle"] + random.randint(-2, 4)))

        return {
            "connected": False,  # indica que é modo demo
            "rpm": s["rpm"],
            "speed_kmh": s["speed"],
            "engine_temp_c": 87,
            "fuel_percent": 67,
            "throttle_percent": s["throttle"],
            "battery_v": 13.2,
            "intake_temp_c": 34,
            "engine_load_percent": round(30 + s["throttle"] * 0.4),
            "maf_gs": round(3.5 + s["rpm"] / 1000, 1),
            "o2_voltage_v": round(0.1 + random.random() * 0.8, 2),
            "fuel_trim_short_percent": round(random.uniform(-5, 5), 1),
            "fuel_trim_long_percent": round(random.uniform(-3, 3), 1),
            "dtc_codes": [],
            "mil_on": False,
            "timestamp": time.time(),
        }


if __name__ == "__main__":
    # Teste rápido: roda "python obd_reader.py" e mostra leituras a cada 2s
    logging.basicConfig(level=logging.INFO)
    reader = OBDReader()  # sem portstr = auto-detect
    print("Modo demo?" , reader.demo_mode)
    try:
        while True:
            print(reader.get_snapshot())
            time.sleep(2)
    except KeyboardInterrupt:
        print("Encerrado.")
