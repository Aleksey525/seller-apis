import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page: str, campaign_id: str, access_token: str) -> list:
    """Получить список товаров Яндекс маркет.

    Args:
        arg1 (str): Страница с товарами.
        arg2 (str): Идентификатор компании или склада клиента для модели работы с Яндекс маркетом.
        arg3 (str): Api-токен.

    Returns:
        list: Список с товарами клиента.

    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks: list, campaign_id: str, access_token: str) -> dict:
    """Обновить остатки.

    Args:
        arg1 (list): Список с остатками часов.
        arg2 (str): Идентификатор компании или склада клиента для модели работы с Яндекс маркетом.
        arg3 (str): Api-токен.

    Returns:
        dict: Словарь с информацией об остатках.

    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices: list, campaign_id: str, access_token: str) -> dict:
    """Обновить цены товаров.

    Args:
        arg1 (list): Список с ценами часов
        arg2 (str): Идентификатор компании клиента для модели работы с Яндекс маркетом.
        arg3 (str): Api-ключ

    Returns:
        dict: Словарь с информацией об обновленных ценах

    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id: str, market_token: str) -> list:
    """Получить артикулы товаров Яндекс маркета.

    Args:
        arg1 (str): Идентификатор компании или склада клиента для модели работы с Яндекс маркетом.
        arg2 (str): Api-токен.

    Returns:
        list: Список с артикулами часов.
    """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants: list, offer_ids: list, warehouse_id: str) -> list:
    """Создать список с остатками товара с SCU идентификаторами.

    Args:
        arg1 (lst): Список с остатками часов
        arg2 (str): Список c id часов.
        arg3 (str): Идентификатор компании или склада клиента для модели работы с Яндекс маркетом.

    Returns:
        list: Список с остатками часов и их SCU идентификаторами.
    """
    # Уберем то, что не загружено в market
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants: list, offer_ids: list) -> list:
    """Создать список с ценами.

    Args:
        arg1 (list): Список с остатками часов.
        arg2 (str): Список с артикулами часов.

    Returns:
        list: Список с ценами часов.

    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants: list, campaign_id: str, market_token: str) -> list:
    """Загрузить цены.

    Args:
        arg1: (lst): Список с остатками часов.
        arg2 (str): Идентификатор компании или склада клиента для модели работы с Яндекс маркетом.
        arg3 (str): Api-токен.

    Returns:
        list: Список с ценами часов.

    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants: list, campaign_id: str, market_token: str, warehouse_id: str) -> tuple:
    """Загрузить остатки.

    Args:
        arg1: (lst): Список с остатками часов.
        arg2 (str): Идентификатор компании клиента для модели работы с Яндекс маркетом.
        arg3 (str): Api-ключ.
        arg4 (str): Идентификатор склада клиента для модели работы с Яндекс маркетом.

    Returns:
        tuple: остатки часов.

    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        # FBS
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        # Обновить остатки FBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        # Поменять цены FBS
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        # DBS
        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        # Обновить остатки DBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        # Поменять цены DBS
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
