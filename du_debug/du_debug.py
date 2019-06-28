import sys
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF


def main():
    logging.register_options(CONF)
    logging.set_defaults()
  
    grp = cfg.OptGroup('mygroup')
	 

    CONF(sys.argv[1:])

    print "Hello world, all the packets are correct"

def create_server(conf)
	

if __name__ == '__main__':
    main()
