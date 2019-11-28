
#define _GNU_SOURCE

#include "math.h"

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <err.h>
#include <sys/mman.h>

#include "os.h"


#include <inttypes.h>
#include <execinfo.h>
#include <time.h>

#define VPN_MASK 0x1FFFFFFFFFFF
#define PPN_MASK 0xFFFFFFFFFFFFF

/* 2^20 pages ought to be enough for anybody */
#define NPAGES	(1024*1024)
#define EXIT_FAILURE 1
#define EXIT_SUCCESS 0

static void* pages[NPAGES];

uint64_t alloc_page_frame(void)
{
	static uint64_t nalloc;
	uint64_t ppn;
	void* va;

	if (nalloc == NPAGES)
		errx(1, "out of physical memory");

	/* OS memory management isn't really this simple */
	ppn = nalloc;
	nalloc++;

	va = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
	if (va == MAP_FAILED)
		err(1, "mmap failed");

	pages[ppn] = va;	
	return ppn;
}

void* phys_to_virt(uint64_t phys_addr)
{ // takes phys_addr , a physical address, go to the page of the given page number, and on to it's offset.
  // returns the address in memory of this.
	uint64_t ppn = phys_addr >> 12;
	uint64_t off = phys_addr & 0xfff;
	void* va = NULL;

	if (ppn < NPAGES)
		va = pages[ppn] + off;

	return va;
}

// TESTS FUNCTIONS

//void assert_equal(uint64_t received, uint64_t expected) {
//	static int counter = 0;
//
//	if (expected != received) {
//		printf("\n\033[0;31mFailed test!\nExpected \033[0m\033[0;32m%"PRIx64"\033[0m\033[0;31m)"
//				" and received \033[0m\033[0;33m%"PRIx64"\033[0m\033[0;31m.\033[0m\n", expected, received);
//
//		void* callstack[128];
//  		int i, frames = backtrace(callstack, 128);
//  		char** strs = backtrace_symbols(callstack, frames);
//		printf("\033[0;36m(Almost readable) stacktrace\n");
//  		for (i = 0; i < frames; ++i) {
//    			printf("%s\n", strs[i]);
//  		}
//		printf("\033[0m\n");
//  		free(strs);
//
//		assert(0);
//	}
//
//	if (counter % 500 == 0)
//		printf("\033[0;32m.\033[0m");
//	counter++;
//}
//
//uint64_t get_random(uint64_t mask) {
//	return (uint64_t) rand() & mask;
//}
//
//
//int in_array(uint64_t *arr, int size, uint64_t value) {
//	for (int i = 0; i < size; i++)
//		if (arr[i] == value)
//			return 1;
//	return 0;
//}
//
//
//void get_random_list(uint64_t **out, int size, uint64_t mask) {
//	*out = calloc(size, sizeof(uint64_t));
//	uint64_t *arr = *out;
//	int count = 0;
//	uint64_t val;
//
//	while (count < size) {
//		val = get_random(mask);
//
//		if (!in_array(arr, count, val)) {
//			arr[count] = val;
//			count++;
//		}
//	}
//}
//
//uint64_t get_random_vpn() {
//	return (uint64_t) get_random(VPN_MASK);
//}
//
//uint64_t get_random_ppn() {
//	return (uint64_t) get_random(VPN_MASK);
//}
//
//void update_random_and_check(uint64_t pt) {
//	uint64_t vpn = get_random_vpn();
//	uint64_t ppn = get_random_ppn();
//
//	if (rand() % 10 < 3)
//		ppn = NO_MAPPING;
//
//	page_table_update(pt, vpn, ppn);
//	assert_equal(page_table_query(pt, vpn), ppn);
//}
//
//void update_many_with_prefix(uint64_t pt) {
//	int prefix = (rand() % 45) + 1;
//	uint64_t mask = pow(2, prefix + 1) - 1;
//	uint64_t vpn_mask = pow(2, (45 - prefix) + 1) - 1;
//	int amount = (rand() % 20) + 2;
//
//	if (amount > vpn_mask / 2)
//		amount = vpn_mask / 2;
//
//	uint64_t block = get_random(mask) << prefix;
//	uint64_t* vpn_arr;
//	uint64_t* ppn_arr = malloc(sizeof(uint64_t) * amount);
//
//	get_random_list(&vpn_arr, amount, vpn_mask);
//	for (int i = 0; i < amount; i++) {
//		vpn_arr[i] = block + vpn_arr[i];
//		ppn_arr[i] = get_random_ppn();
//
//		page_table_update(pt, vpn_arr[i], ppn_arr[i]);
//		assert_equal(page_table_query(pt, vpn_arr[i]), ppn_arr[i]);
//	}
//
//	for (int i = 0; i < amount; i++) {
//		uint64_t value = page_table_query(pt, vpn_arr[i]);
//		uint64_t expected = ppn_arr[i];
//		if (value != expected) {
//			printf("Set values:\n");
//			for (int j = 0; j < amount; j++)
//				printf("page_table[%"PRIx64"] = %"PRIx64"\n", vpn_arr[j], ppn_arr[j]);
//			printf("\nFailed on index %d,\ngot value %"PRIx64" instead of %"PRIx64"\n", i, value, expected);
//			assert(0);
//		}
//	}
//
//	free(vpn_arr);
//	free(ppn_arr);
//}
//
//void perform_random_move(uint64_t pt) {
//	int option = rand() % 2;
//
//	switch (option) {
//		case 0:
//			update_random_and_check(pt);
//			break;
//		case 1:
//			update_many_with_prefix(pt);
//			break;
//	}
//
//}

void tester_update_ppn_mapping(uint64_t* vpn_slicing, uint64_t* new_pt, uint64_t ppn){
    // Helper function for tester_page_table_update()
    // new_pt - the address in memory of the page table
    int i;
    uint64_t vpn_slice=0, alloc_page, new_pt_frame_num;
    for (i=0; i<5; i++){
        vpn_slice=vpn_slicing[i];
        if(new_pt[vpn_slice]%2==0){ // Go to pt and check if it's valid (LSB is 1). if not, allocate
            if(i!=4){
                alloc_page = alloc_page_frame();
                new_pt[vpn_slice] = (alloc_page<<12)+1; // change Valid bit to 1
            }
        }
        if(i==4){
            break;
        }
        // Get the address in the current page table where the current VA subset says, and take the page table in it.
        new_pt_frame_num = new_pt[vpn_slice] >> 12;
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
//        new_pt = phys_to_virt(new_pt[vpn_slice]-1);
        // bits 1-11 are always 0! and bit 0 is the VALID thing, which is always 1 in this point, so remove this bit!
    }
    new_pt[vpn_slice] = (ppn<<12)+1; // change Valid bit to 1
}


void tester_destroy_mapping(uint64_t* vpn_slicing, uint64_t* new_pt){
    // Helper function for tester_page_table_update()
    int i;
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2==0){
            return;
        }
        if(i==4){
            break;
        }
        new_pt = phys_to_virt(new_pt[vpn_slice]-1);
    }
    new_pt[vpn_slice]-=1; // change Valid bit to 0
}


void tester_page_table_update(uint64_t pt, uint64_t vpn, uint64_t ppn){
    // An implementation of a working page_table_update() function
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL;
    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat
    if (ppn==NO_MAPPING){
        tester_destroy_mapping(vpn_slicing, new_pt);
    }
    else{
        tester_update_ppn_mapping(vpn_slicing, new_pt, ppn);
    }
}


uint64_t tester_page_table_query(uint64_t pt, uint64_t vpn){
    // An implementation of a working page_table_query() function
    int i;
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t vpn_slice=0, *new_pt=NULL;
    new_pt = phys_to_virt(pt<<12);
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2 == 0){
            return NO_MAPPING;
        }
        if(i==4){
            break;
        }
        new_pt = phys_to_virt(new_pt[vpn_slice]-1); // returns the address in memory
    }
    return (new_pt[vpn_slice])>>12;
}



int test_sanity_check(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    if(page_table_query(pt, vpn) != NO_MAPPING){
        printf("basic functionality fails. \n");
        return 1;
    }
    page_table_update(pt, vpn, ppn);
	if(page_table_query(pt, vpn) != ppn) {
	    printf("basic functionality fails. \n");
	    return 1;
	}
	page_table_update(pt, vpn, NO_MAPPING);
	if(page_table_query(pt, vpn) != NO_MAPPING) {
	    printf("basic functionality fails. \n");
	    return 1;
	}

	return 0;
}

// TESTS FOR page_table_update():

int test_override_mapping(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests a mapping that was overriden with another ppn */
    uint64_t different_ppn = 0xabaa1;
    page_table_update(pt, vpn, ppn);
	if(tester_page_table_query(pt, vpn) != ppn) {
	    printf("basic functionality fails. \n");
	    return 1;
	}
	page_table_update(pt, vpn, different_ppn); // a different ppn
	if(tester_page_table_query(pt, vpn) != different_ppn) {
	    printf("test_override_mapping failed. \n");
	    return 1;
	}

	return 0;
}


int test_override_prefix_similar_vpn(uint64_t pt) {
    /* Tests a mapping of an address that shares a prefix with a previously mapped address.
       test if the first vpn is still mapped, in a way that the second didn't overridden its earlier PTE's
    */
    uint64_t ppn = 0xfff;
    uint64_t different_ppn = 0xabaa1;
    uint64_t vpn_prefix = (0x0123456789abc << 12);
    uint64_t vpn = vpn_prefix | 0xabc;
    uint64_t similar_prefix_vpn = vpn_prefix | 0x123;

    page_table_update(pt, vpn, ppn); // map a vpn
	if(tester_page_table_query(pt, vpn) != ppn) {
	    return 1;
	}
	page_table_update(pt, similar_prefix_vpn, different_ppn); // map a vpn with a similar prefix
	if(tester_page_table_query(pt, similar_prefix_vpn) != different_ppn) {
	    return 1;
	}
    if(tester_page_table_query(pt, vpn) != ppn) { // check if first vpn not overridden
    printf("test_override_prefix_similar_vpn failed. \n");
	    return 1;
	}
	return 0;
}


int get_leaf_valid_bit(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    // iterates on the Page Tables, and returns 
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL;
    int valid_bit;

    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat
    if(new_pt == NULL) {
            return EXIT_FAILURE
        }
    int i;
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2==0){
            return EXIT_FAILURE;
        }
        if(i==4){
            break;
        }
        new_pt_frame_num = new_pt[vpn_slice] >> 12; // need to pass to phys_to_virt() without any offset.
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
        if(new_pt == NULL) {
            return EXIT_FAILURE
        }

    }
    valid_bit = new_pt[vpn_slice] & 0x1;
    return valid_bit; // change Valid bit to 0
}

int test_mark_leaf_invalid() {

}




int POINTS_DEDUCTION_PER_TEST = 5;
int main(int argc, char **argv)
{
    uint64_t pt = alloc_page_frame(); // the physical page number of this frame
    int student_grade = 100;
    if(test_sanity_check(pt, 0xcafe, 0xf00d) == 1) {
        return 1;
    }

    if(test_override_mapping(pt, 0xffff1, 0xaaa) == 1) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(test_override_prefix_similar_vpn(pt) == 1) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(test_override_prefix_similar_vpn(pt) == 1) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }


    printf("grade is: %d\n", student_grade);


//    assert(page_table_query(pt, 0x100001) == NO_MAPPING); // address which is bigger then 2^20


//	srand(time(NULL));
//	page_table_update(pt, 0xcafe, 0xf00d);
//
//	printf("hi 1\n\n");
//	assert(page_table_query(pt, 0xcafe) == NO_MAPPING);
//	printf("\nhi 2\n\n");
//	page_table_update(pt, 0xcafe, 0xf00d);
//	printf("\nhi 3\n\n");
//	assert(page_table_query(pt, 0xcafe) == 0xf00d);
//	printf("\nhi 4\n\n");
//	page_table_update(pt, 0xcafe, NO_MAPPING);
//	printf("\nhi 5\n\n");
//	assert(page_table_query(pt, 0xcafe) == NO_MAPPING);
//	printf("\nhi 6\n\n");
//
//
//	for (int i = 0; i < pow(2, 15); i++) {
////		printf("i = %d\n", i);
//		perform_random_move(pt);
//	}
//	printf("\nAll tests passed!\n");
//
//	printf("done\n");
	return 0;
}

