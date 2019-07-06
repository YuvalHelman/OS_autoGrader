#include "message_slot.h"

#include <fcntl.h>      /* open */
#include <unistd.h>     /* exit */
#include <sys/ioctl.h>  /* ioctl */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

int main(int argc, char *argv[]) {
	if (argc < 3) {
		printf("Bad params!\n");
		exit(EXIT_FAILURE);
	}
	char* messageSlotFilePath = argv[1];
	char *ptr;
	unsigned int channelId = strtoul(argv[2], &ptr, 10);
	char* msg = (char *) malloc(BUF_LEN);

	int file_desc;
	int ret_val;

	file_desc = open(messageSlotFilePath, O_RDWR);
	if (file_desc < 0) {
		printf("Can't open device file: %s\n", messageSlotFilePath);
		exit(-1);
	}

	ret_val = ioctl(file_desc, MSG_SLOT_CHANNEL, channelId);
	if (ret_val) {
		printf("Could not change channel. %s\n", strerror(errno));
		exit(EXIT_FAILURE);
	}

	ret_val = read(file_desc, msg, BUF_LEN);
	if (ret_val <= 0) {
		printf("Could not read from channel. %s\n", strerror(errno));
		exit(EXIT_FAILURE);
	}

	printf("%s", msg);
	close(file_desc);
	return ret_val;
}
