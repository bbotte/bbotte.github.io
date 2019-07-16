import logging
import logging.config

# logger configuration
logging.config.dictConfig({
  'version': 1,
  'disable_existing_loggers': False,  # this fixes the problem

  'formatters': {
    'my_verbose_formatter': {
      'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
      },
    },
  'handlers': {
    'my_verbose_handler': {
      'level':'DEBUG',
      'class':'logging.StreamHandler',
      'formatter': 'my_verbose_formatter'
      },

    },
  'loggers': {
    'verbose': {
      'handlers': ['my_verbose_handler'],
      'level': 'DEBUG',
      'propagate': True
    }
  }
})

