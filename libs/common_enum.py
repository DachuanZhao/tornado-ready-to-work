import enum,abc

class CustomIntEnum(enum.IntEnum):
    """
    抽象基类，强制__str__方法，并且定义好to_frontend_dict方法
    """

    @abc.abstractmethod
    def __str__(self):
        """
        此方法用来得到单个的int->前端
        """
        pass

    @classmethod
    def to_frontend_dict(cls):
        """
        此方法用来得到所有的int->前端
        """
        return {member.value:str(member) for _,member in cls.__members__.items() if member.value> 0}

    @classmethod
    def to_frontend_list(cls):
        """
        此方法用来得到所有的int->前端
        """
        temp_list = []
        for _,member in cls.__members__.items():
            if member.value > 0:
                temp_dict = {}
                #后端存的id
                temp_dict["id"] = member.value
                #前端展示的value
                temp_dict["value"]=str(member)
                temp_list.append(temp_dict)
        return temp_list



@enum.unique
class UserStatus(CustomIntEnum):
    """
    用户的状态
    """
    GENERAL = 1
    LOCKED = 2

    def __str__(self):
        __frontend_dict = {
            "GENERAL":"正常",
            "LOCKED":"锁定",
                }
        return __frontend_dict[self.name]