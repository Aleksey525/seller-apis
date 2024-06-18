## seller.py
Скрипт для обновления цен и остатков товара (часы casio) на маркетплейсе [ozon.ru](https://ozon.ru). 
Для запуска скрипта необходимо получить `API-токен` от маркетплейса.

После запуска скрипт создает список с артикулами товаров продавца на `Ozon`. Далее загружает и обрабатывает актуальную
информацию о ценах и остатках товара с сайта [timeworld.ru](https://timeworld.ru), затем отбирает товары по ранее полученным
артикулам. И обновляет цены и остатки товара на `Ozon`.

## market.py
Скрипт для обновления цен и остатков товара (часы casio) на маркетплейсе [market.yandex.ru](https://market.yandex.ru).
Для запуска скрипта необходимо получить `API-токен` от маркетплейса.

Скрипт работает с `FBS` и `DBS` моделями взаимодействия продавца и маркетплейса. Загружает и обрабатывает актуальную
информацию о ценах и остатках товара с сайта [timeworld.ru](https://timeworld.ru). Формирует SKU товаров на маркетплейсе
из ранее полученной информации о товаре. Затем обновляет цены и осатки товара.