#### 1 命名



##### 1.1 应该避免的名称

1. 单字符名称，除了计数器和迭代器

2. 包、模块中的连接字符(-)

3. 双下划线开头结尾的名称(如\__init__)

   

##### 1.2 命名约定

- 所谓”内部(Internal)”表示仅模块内可用, 或者, 在类内是保护或私有的

- 用单下划线(_)开头表示模块变量或函数是protected的(使用import * from时不会包含)

- 用双下划线(__)开头的实例变量或方法表示类内私有

- 将相关的类和顶级函数放在同一个模块里. 不像Java, 没必要限制一个类一个模块

- 对类名使用大写字母开头的单词(如CapWords, 即Pascal风格), 但是模块名应该用小写加下划线的方式(如lower_with_under.py)。尽管已经有很多现存的模块使用类似于CapWords.py这样的命名, 但现在已经不鼓励这样做, 因为如果模块名碰巧和类名一致, 这会让人困扰

  

##### 1.3 推荐命名规范

​          类别                                    解释                               推荐命名方式                                           示例写法

- Modules                               模块                    英文小写并通过下划线连接                           lower_with_under

- Packages                               包                      英文小写并通过下划线连接                            lower_with_under

- Classes                                  类                      大驼峰                                                               CapWords

- Exceptions                           异常                   大驼峰                                                               CapWords

- Functions                             函数                   英文小写并通过下划线连接外加小号             lower_with_under()

- Global/Class Constants     全局/类常量      英文大写并通过下划线连接                            CAPS_WITH_UNDER

- Global/Class Variables       全局/类常量      英文小写并通过下划线连接                            lower_with_under

- Instance Variables              实例变量           英文小写并通过下划线连接                            lower_with_under

- Method Names                   方法/属性         英文小写并通过下划线连接外加小括号         lower_with_under() 

- Function/Method Parameters    参数        英文小写并通过下划线连接                            lower_with_under

- Local Variables                    局部变量          英文小写并通过下划线连接                            lower_with_under

  

##### 1.4 导入格式

导入总应该放在文件顶部, 位于模块注释和文档字符串之后, 模块全局变量和常量之前。 导入应该按照从最通用到最不通用的顺序分组，推荐导入顺序如下：

1. 标准库导入(通常为Python内置模块)
2. 第三方依赖导入(通过Python包管理工具如pip、conda等安装的依赖)
3. 自定义包或者模块导入

示例如下：

注：students.py、books.py 为用户自定义模块

~~~python
#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import random
from functools import reduce

import requests
import numpy as np

from students.py import Student
from books.py import Book
~~~



#### 2 编码



##### 2.1 代码行

- 尽量不要在代码行的末尾加分号，也不要用分号将两条命令放在同一行
- 每行不超过80字符 例外情况：1.长的导入模块语句 2.注释里的url
- 不要使用反斜杠连接行

Python会将圆括号中括号和花括号中的行隐式的连接起来，故可以以此特性在表达式外围增加一对额外的圆括号。

~~~python
Yes: foo_bar(self, width, height, color='black', design=None, x='foo',
             emphasis=None, highlight=0)

     if (width == 0 and height == 0 and
         color == 'red' and emphasis == 'strong'):
~~~

如果一个文本字符串在一行放不下, 可以使用圆括号来实现隐式行连接:

~~~python
x = ('This will build a very long long '
     'long long long long long long string')
~~~

在注释中，如果必要，将长的URL放在一行上，下面示范错误写法。

~~~python
No:  # See details at
     # http://www.example.com/us/developer/documentation/api/content/\
     # v2.0/csv_file_name_extension_full_specification.html
~~~

##### 2.2 缩进

养成用4个空格代替缩进代码。不推荐使用tab,也不要混用tab与空格。对于行连接的情况建议采用垂直对齐换行，或者使用4空格的悬挂式缩进(注：此时第一行不应该有参数)

~~~python
Yes:   # Aligned with opening delimiter
       foo = long_function_name(var_one, var_two,
                                var_three, var_four)

       # Aligned with opening delimiter in a dictionary
       foo = {
           long_dictionary_key: value1 +
                                value2,
           ...
       }

       # 4-space hanging indent; nothing on first line
       foo = long_function_name(
           var_one, var_two, var_three,
           var_four)

       # 4-space hanging indent in a dictionary
       foo = {
           long_dictionary_key:
               long_dictionary_value,
           ...
       }
 

No:    # Stuff on first line forbidden
      foo = long_function_name(var_one, var_two,
          var_three, var_four)

      # 2-space hanging indent forbidden
      foo = long_function_name(
        var_one, var_two, var_three,
        var_four)

      # No hanging indent in a dictionary
      foo = {
          long_dictionary_key:
              long_dictionary_value,
              ...
      }
~~~

##### 2.3 空行与空格

**顶级定义之间空两行，方法定义之间空一行**

顶级定义之间空两行, 比如函数或者类定义、方法定义，类定义与第一个方法之间， 都应该空一行。 函数或方法中， 可以根据可读性适当的选择空一行。

**按照标准的排版规范来使用标点两边的空格**

括号内不要有空格

~~~
Yes: spam(ham[1], {eggs: 2}, [])
No:  spam( ham[ 1 ], { eggs: 2 }, [ ] )
~~~

