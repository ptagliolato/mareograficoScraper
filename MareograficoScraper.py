import warnings
from typing import Tuple, List

import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, quote
import pandas as pd
import numpy as np

class MareograficoScraper:

    @staticmethod
    def available_networks(html: str = None) -> dict:
        """
        return dictionary {network_label: network_id, ...}
        :param html:
        :return:
        """
        # TODO: need css selector and html scraping to automatize
        if not html:
            d = {"National Tide Gauge Network": 1,
                 "National Wave Buoy Network": 4,
                 "ADSP MAC Network": 9,
                 }
            return d
        else:
            raise NotImplementedError()

    @staticmethod
    def get_base_response():
        url = "https://www.mareografico.it/en/stations.html"
        return requests.get(url)


    @staticmethod
    def get_network_response(network_id: int, base_response=None) -> requests.models.Response:
        """
        http workflow to obtain the page for scraping a network given its network_id.
        Note: The resulting webpage is that of the default (first) station in the network.
        :param network_id:
        :param base_response:
        :return:
        """
        assert network_id in list(MareograficoScraper.available_networks().values()), "id must be in available_networks"
        url = "https://www.mareografico.it/en/stations.html"
        if base_response is None:
            base_response = MareograficoScraper.get_base_response()
        # res1.headers
        session_id = base_response.cookies.get("PHPSESSID")

        # cookie that controls the selected network (e.g. wave buoy = 4)
        network_selector_id = f"MG{session_id}"  # cookie name

        # get and modify cookie value
        network_selector = base_response.cookies.get(network_selector_id)  # cookie (encoded) value
        deparsed_network_selector = unquote(network_selector)  # cookie (decoded) value
        # quote(deparsed_network_selector)==network_selector # check inverse transform

        array_network_selector = deparsed_network_selector.split(
            "][")  # cookie value to array (position for network is 1 in the resulting array)
        # "][".join(array_network_selector) == deparsed_network_selector # check inverse transform

        ar2 = array_network_selector.copy()
        ar2[1] = str(network_id)  # 4 corresponds to the buoy network

        # re-encode the cookie value
        network_selector_new_value = quote("][".join(ar2))

        # res1.cookies.pop()
        cookies1: requests.cookies.RequestsCookieJar = base_response.cookies.copy()
        # c1=res1.cookies.copy()
        # q1=c1.pop(network_selector_id)
        # c1
        cookies1.pop(network_selector_id)
        cookies1.set(network_selector_id, network_selector_new_value)
        # NOTE: valutare se serva impostare domain come nel cookie tirato fuori con il pop. In tal caso capire come fare.

        res2 = requests.get(url, cookies=cookies1)
        return res2


    @staticmethod
    def available_stations(html_network_text: str) -> List[Tuple[int, str]]:
        '''
        return dictionary {station_name: station_id, ...}

        :param html_network_text: html of the webpage of a network (i.e. after first step)
        :return:
        '''
        # assert network_id in list(available_networks().values()), "id must be in available_networks"
        soup = BeautifulSoup(html_network_text)
        tags = soup.select("div.dM > ul > li")
        res = list()
        for tag in tags:
            res.append((tag['id'],tag.text))
        return res



    @staticmethod
    def scrape_all_stations():
        #keys:list[tuple(int,int)]
        base_response = MareograficoScraper.get_base_response()
        #networks_col=list()
        stations_col=list()
        res=list()
        ndict=MareograficoScraper.available_networks()
        for network_label in list(ndict.keys()):
            #network_label=list(ndict.keys())[0]
            network_id=ndict[network_label]
            res_network = MareograficoScraper.get_network_response(network_id, base_response)
            stations = MareograficoScraper.available_stations(res_network.text)
            res.extend([(network_id, network_label, el[0], el[1]) for el in stations])
        return res


