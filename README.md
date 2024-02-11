## ZONT для Home Assistant

![python version](https://img.shields.io/badge/Python-3.11-yellowgreen?style=plastic&logo=python)
![pydantic version](https://img.shields.io/badge/pydantic-ha-yellowgreen?style=plastic&logo=fastapi)
![aiohttp version](https://img.shields.io/badge/aiohttp-ha-yellowgreen?style=plastic)
![Home Assistant](https://img.shields.io/badge/HomeAssistant-latest-yellowgreen?style=plastic&logo=homeassistant)


[![Donate](https://img.shields.io/badge/donate-Tinkoff-FFDD2D.svg)](https://www.tinkoff.ru/rm/shutov.mikhail19/wUyu873109)

## Описание
Компонент для управления устройствами [ZONT](https://zont-online.ru/) из Home Assistant. 

Для входа в ваш аккаунт потребуется токен. Его можно получить из Home Assistant.
При добавлении устройства нажмите галочку "Получить токен". При каждом получении токена
создаётся новый. Что бы их не плодить на аккаунте ZONT, запишите полученный токен.
Как удалить токен описано [здесь](https://lk.zont-online.ru/widget-api/v2).

После авторизации в Home Assistant (далее НА) добавляются все устройства аккаунта.

*Модели контроллеров на которых проверена работоспособность:*
* *CLIMATIC*
* *H2000+ pro*
* *H2000+*
* *H2000*
* *H1000*
* *H1000+*

*Модели термостатов на которых проверена работоспособность:*
* *T100 (H-1)*
* *T102 (H-2)*

`* на данный момент устройства термостат не передают котловые сенсоры`

## Возможности
В НА из ZONT добавляются следующие объекты каждого устройства:
* Контуры отопления
* Сенсоры
* Кастомные элементы (кнопка или сложная кнопка)
* Охранные зоны
* Состояние и местоположение автомобиля

### Контуры отопления.
Контур отопления добавляется в НА в виде термостата. Все, созданные в ZONT, режимы отопления добавляются в НА.

Называйте контуры отопления в ZONT осмысленно. От названия контура зависят пределы регулировки температуры.

Например, если контур отопления тёплого пола, то в названии должно быть слово "пол", а для контура ГВС - "гвс", "вода".

### Сенсоры.
В НА добавляются все доступные сенсоры в API ZONT.
Обновление сенсоров происходит примерно раз в минуту. 
По этой причине нет смысла в таких бинарных сенсорах как датчик движения и датчик открытия двери. 

### Кастомные элементы.
В веб интерфейсе ZONT можно добавить элементы управления и привязать на них любое доступное действие.
Например, включить реле или выключить реле, включить котловой режим, включить отопительный режим на всех устройствах и др.
Смотрите возможности в интерфейсе ZONT.

### Охранные зоны.
В НА добавляются все охранные зоны устройства. Можно поставить на охрану или снять с охраны охранную зону.

### Состояние и местоположение автомобиля.
Добавляются бинарные датчики автомобиля, его местоположение. Есть возможность постановки и снятия с охраны.
С помощью кастомного элемента можно организовать запуск двигателя и др.

<details>

<summary>Бинарные датчики автомобиля тут</summary>

- Двигатель заведён
- Состояние блокировки двигателя
- Состояние сирены
- Передняя левая дверь открыта
- Передняя правая дверь открыта
- Задняя левая дверь открыта
- Задняя правая дверь открыта
- Багажник открыт
- Капот открыт

</details>


> У меня нет автосигнализации ZONT, поэтому реальных тестов не проводилось. 
> Если будет у когда желание и сигнализация, то пишите, проверим.


## Установка
**Способ 1.** [HACS](https://hacs.xyz/) -> Интеграции -> 3 точки в правом верхнем углу -> Пользовательские репозитории

Далее вставляем репозиторий https://github.com/MihVS/zont_ha выбираем категорию "Интеграция" и жмём добавить.
***
**Способ 2.** Вручную скопируйте каталог `zont_ha` в директорию `/config/custom_components`
***
**Не забываем поставить ★ интеграции.**

## Настройка
> Настройки -> Интеграции -> Добавить интеграцию -> **ZONT**
 
Если интеграции не появилось в списке, то очистите кэш в браузере.

### Логирование.
Чтобы изменить уровень логирования, для выявления проблем, необходимо в файле `configuration.yaml` добавить:
```yaml
logger:
  logs:
    custom_components.zont_ha: debug
```

## Разработчик
**[Михаил Шутов](https://github.com/mihvs)**
