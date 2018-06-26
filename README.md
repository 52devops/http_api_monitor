# http_api_monitor
* 通过logstash收集nginx log到es中，将nginx日志进行处理后对url和参数进行处理拆分，详见logstash.conf
* 将处理后的日志根据定义好的elasticsearch template进行生产index存储，详见template.json
* 通过python脚本定时处理index内文档内容后进行上报falcon,详见http_api_monitor.py  
* 设置好falcon template发送报警  
# 报警项：
* 一分钟内单个接口响应大于2秒(可在配置文件中指定)的请求次数 
* 一分钟内单个接口请求大于2秒(可在配置文件中指定)的请求次数 
* 一分钟内单个接口请求为404的请求次数
* 一分钟内单个接口请求为408的请求次数 
* 一分钟内单个接口请求为499的请求次数 
* 一分钟内单个接口请求为500的请求次数 
* 一分钟内单个接口请求为502的请求次数 
* 一分钟内单个接口请求为504的请求次数 
