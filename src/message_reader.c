#include "message_slot.h"

#include <fcntl.h>      /* open */
#include <unistd.h>     /* exit */
#include <sys/ioctl.h>  /* ioctl */
#include <stdio.h>
#include <stdlib.h>

#define ARGS_COUNT 3
#define BUFF_SIZE 129

int main(int argc, const char* argv[]){
  int file_desc;
  int ret_val;
  char buff[BUFF_SIZE];

  if (argc != ARGS_COUNT){
    printf("Invalid number of args, should be %d received %d\n", ARGS_COUNT, argc);
    return -1;
  }

  file_desc = open( argv[1], O_RDONLY );
  if( file_desc < 0 )
  {
    printf("Can't open device file: %s\n", argv[1]);
    return -1;
  }

  ret_val = ioctl( file_desc, MSG_SLOT_CHANNEL, atoi(argv[2]));
  if (ret_val < 0){
    perror("Failed to ioctl\n");
	close(file_desc);
    return -1;
  }

  ret_val = read( file_desc, buff, BUFF_SIZE);
  if (ret_val < 0){
    perror("Failed to read\n");
	close(file_desc);
    return -1;
  }
  close(file_desc);

  buff[ret_val] = '\0';
  printf("%s", buff);

  return 0;
}
