## ZONT для Home Assistant

![python version](https://img.shields.io/badge/Python-3.12-yellowgreen?style=plastic&logo=python)
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

После авторизации в Home Assistant (далее НА) добавляются все доступные в API устройства аккаунта.

*Модели контроллеров на которых проверена работоспособность:*
* *CLIMATIC*
* *H2000+ pro*
* *H2000+*
* *H2000*
* *H1000*
* *H1000+*

`* Теоретически все модели поддерживаюся интеграцией. В списке устройства с которыми я лично работал.`

*Модели термостатов на которых проверена работоспособность:*
* *T100 (H-1)*
* *T102 (H-2)*

`* на данный момент устройства термостат не передают котловые сенсоры`

## Возможности
В НА из ZONT добавляются следующие объекты каждого устройства:
* [Контуры отопления](#контуры-отопления)
* [Сенсоры](#сенсоры)
* [Кастомные элементы](#кастомные-элементы) (кнопка или сложная кнопка)
* [Охранные зоны](#охранные-зоны)
* [Местоположение](#местоположение)
* [Состояние и местоположение автомобиля](#состояние-и-местоположение-автомобиля)

### Контуры отопления.
Контур отопления добавляется в НА в виде термостата. Шаг регулировки температуры и пределы регулировки берутся из аккаунта ZONT. 
Все, созданные в ZONT, режимы отопления добавляются в НА. В каждом контуре есть возможность менять режим отопления.
Для изменения режима отопления во всех контурах одновременно в НА добавляются кнопки с названиями режимов.
> [!WARNING]
> Включение и выключение контура возможно только через режимы отопления. 
> Управление контуром в НА через set_hvac_mode не предусмотрено. 
> Такова особенность ZONT.

### Сенсоры.
В НА добавляются все доступные сенсоры в API ZONT.
Обновление сенсоров происходит примерно раз в минуту. 

У радиодатчиков есть дополнительные параметры rssi и вольтаж батарейки. Эти параметры 
добавляются в виде отдельных сенсоров с тем же названием, что и сам датчик.

Ошибки котла добавляются отдельным сенсором, который отображает код ошибки и описание.
Описание ошибок зависит от котла.

### Кастомные элементы.
В веб интерфейсе ZONT можно добавить элементы управления и привязать на них любое доступное действие.
Например, включить реле или выключить реле, включить котловой режим, включить отопительный режим на всех устройствах и др.
Смотрите возможности в интерфейсе ZONT.
> [!WARNING]
> В настройках ZONT кастомного элемента должна быть снята галочка в пункте:
> - [ ] Скрывать виджет на панели состояния

### Охранные зоны.
В НА добавляются все охранные зоны устройства. Можно поставить на охрану или снять с охраны охранную зону.

### Местоположение
Передаётся местоположение устройства.

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
> Если будет у кого желание и сигнализация, то пишите, проверим.


## Установка
**Способ 1.** [HACS](https://hacs.xyz/) -> Интеграции -> 3 точки в правом верхнем углу -> Пользовательские репозитории

Далее вставляем репозиторий https://github.com/MihVS/zont_ha выбираем категорию "Интеграция" и жмём добавить.
***
**Способ 2.** Вручную скопируйте каталог `zont_ha` в директорию `/config/custom_components`
***
### **Не забываем поставить ★ интеграции. Это важно для меня.**

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
