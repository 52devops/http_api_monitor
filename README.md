# http_api_monitor
* 通过logstash收集nginx log到es中，将nginx日志进行处理后对url和参数进行处理拆分，详见logstash.conf
* 将处理后的日志根据定义好的elasticsearch template进行生产index存储
* 通过python脚本定时处理index内文档内容后进行上报falcon
* 设置好falcon template发送报警
