import datetime
import inspect
import logging
import os
from enum import Enum
from pathlib import Path
from src.Model.Singleton import Singleton


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logging(metaclass=Singleton):
    """
    A singleton for logging. This ensures there is only one logger
    at any given time that can write to the log file. Logging is done
    by grabbing the Logging instance, e.g., logger = Logging(), and then
    calling logger.log(level, message). Level is the severity of the message.
    Message is the message.

    Log levels are defined by the enum class LogLevel:
        10: DEBUG - detailed information for debugging purposes.
        20: INFO - general messages, e.g. "process succeeded".
        30: WARNING - warning messages, e.g. something unexpected happening,
                      but the program is still working as expected.
        40: ERROR - a serious problem, e.g. the software is unable to perform
                    a function or a function fails.
        50: CRITICAL - a serious error, often to indicate that the program is
                       unable to continue running.

    Messages are formatted as:
        LEVEL [Date Time] File - Function : Message

    Log files are written to the .OnkoDICOM hidden folder, in a subdirectory
    called "Logs". Each file name is simply the date and time that the file
    was first created.

    This class uses Python's built-in logging module. This can write to any
    file, but if you want to write to, for example, a database, then this will
    need to be implemented from scratch.
    """
    def __init__(self):
        """
        Initialise the Logging class.
        """
        # Set the file path for the log
        date_time = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        hidden_folder = Path(os.environ.get("USER_ONKODICOM_HIDDEN"))

        # Create log folder if it doesn't exist
        if not os.path.exists(hidden_folder.joinpath("Logs")):
            os.mkdir(hidden_folder.joinpath("Logs"))

        # Set log file path
        path = hidden_folder.joinpath('Logs', date_time + ".log")

        # Set log level - this is needed as once the log level is set
        # for the logging module, it cannot be reset while the program
        # is running. As such the logging module is set to the lowest
        # level, and we manually decide what to log.
        self.log_level = LogLevel.WARNING

        # Create logger and set settings
        log_format = '%(levelname)s\t[%(asctime)s] %(message)s'
        logging.basicConfig(filename=path, filemode='a', format=log_format,
                            datefmt='%Y-%m-%dT%H-%M-%S', level=logging.DEBUG,
                            force=True)
        self.logger = logging.getLogger('logger')

    def change_log_level(self, level):
        """
        Change the log level.
        :param level: LogLevel type, the level to change logging to.
        """
        self.log_level = level

    def log(self, level, message):
        """
        Logs a message to the log file if the level is the same as or
        higher than the object's currently set log level.
        :param level: The level of the message. A LogLevel member.
        :param message: The message to write to the log file.
        """
        # Return if not the right log level
        if level.value < self.log_level.value:
            return

        # Get date-time, calling function, and calling file
        caller = inspect.stack()[1]
        calling_function = caller.function
        calling_file_path = caller.filename
        calling_file_name = os.path.basename(calling_file_path)

        # Generate the log message
        log_message = calling_file_name + ":" + calling_function \
            + " - " + message

        # Log to file
        self.logger.log(level.value, log_message)
