
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
#define EXIT_FAILED -1
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
    /* Tests the most basic functionality of the functions */
    if(page_table_query(pt, vpn) != NO_MAPPING){
        printf("basic table query failed NO_MAPPING");
        return EXIT_FAILED;
    }
    page_table_update(pt, vpn, ppn);
	if(page_table_query(pt, vpn) != ppn) {
	    printf("basic table query failed after table_update");
	    return EXIT_FAILED;
	}

	page_table_update(pt, vpn, NO_MAPPING);
	if(page_table_query(pt, vpn) != NO_MAPPING) {
	    printf("basic table query failed after NO_MAPPING");
	    return EXIT_FAILED;
	}

	return EXIT_SUCCESS;
}

// TESTS FOR page_table_update():

int test_override_mapping(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests a mapping that was overriden with another ppn */
    uint64_t different_ppn = 0xabaa1;

    page_table_update(pt, vpn, ppn);
	if(tester_page_table_query(pt, vpn) != ppn) {
	    printf("%d", tester_page_table_query(pt, vpn));  // DEBUG
	    printf("test_override_mapping failed{1}. \n");
	    return EXIT_FAILED;
	}
	page_table_update(pt, vpn, different_ppn); // a different ppn
	if(tester_page_table_query(pt, vpn) != different_ppn) {
	    printf("%d", tester_page_table_query(pt, vpn)); // DEBUG
	    printf("test_override_mapping failed{2}. \n");
	    return EXIT_FAILED;
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
	    return EXIT_FAILED;
	}
	page_table_update(pt, similar_prefix_vpn, different_ppn); // map a vpn with a similar prefix
	if(tester_page_table_query(pt, similar_prefix_vpn) != different_ppn) {
	    return EXIT_FAILED;
	}
    if(tester_page_table_query(pt, vpn) != ppn) { // check if first vpn not overridden
    printf("test_override_prefix_similar_vpn failed. \n");
	    return EXIT_FAILED;
	}
	return EXIT_SUCCESS;
}


int get_leaf_valid_bit(uint64_t pt, uint64_t vpn) {
    // iterates on the Page Tables, and returns the valid bit of the PPN from the given VPN location
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL, new_pt_frame_num;
    int valid_bit;

    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat
    if(new_pt == NULL) {
            return EXIT_FAILED;
        }
    int i;
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        if (new_pt[vpn_slice]%2==0){
            return EXIT_SUCCESS;
        }
        if(i==4){
            break;
        }
        new_pt_frame_num = new_pt[vpn_slice] >> 12; // need to pass to phys_to_virt() without any offset.
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
        if(new_pt == NULL) {
            return EXIT_FAILED;
        }

    }
    valid_bit = new_pt[vpn_slice] % 2;
    return valid_bit;
}

int test_mark_leaf_invalid(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests a mapping that was erased is also marked with VALID_BIT=0 */
    page_table_update(pt, vpn, ppn);
	if(tester_page_table_query(pt, vpn) != ppn) {
	    printf("test_mark_leaf_invalid failed{1}. \n");
	    return EXIT_FAILED;
	}
	page_table_update(pt, vpn, NO_MAPPING);
	if(tester_page_table_query(pt, vpn) != NO_MAPPING) {
	    printf("test_mark_leaf_invalid failed{2}. \n");
	    return EXIT_FAILED;
	}
	// Iterate
	int leaf_valid_bit = get_leaf_valid_bit(pt, vpn);
	if(leaf_valid_bit == 1 || leaf_valid_bit == EXIT_FAILED) { // valid bit wasn't turned off together with NO_MAPPING on #frame.
	    printf("test_mark_leaf_invalid failed{3}. \n");
	    return EXIT_FAILED;
	}

	return EXIT_SUCCESS;
}


int test_root_node_not_zero(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests that root PT wasn't assumed to be page 0, but calling sanity_check with a new root PT */
    uint64_t new_pt = alloc_page_frame();

    if(test_sanity_check(new_pt, vpn, ppn) == EXIT_FAILED) {
        return EXIT_FAILED;
    }
	return EXIT_SUCCESS;
}

// TESTS FOR page_table_query():



int test_unmapped_from_each_level(uint64_t pt, uint64_t vpn, uint64_t ppn) {
    /* Tests that the function returns a "NO_MAPPING" value where there's some valid nodes in the way */
    uint64_t vpn_slicing [5] = {(vpn>>35) & 0x1ff,(vpn>>27) & 0x1ff,(vpn>>17) & 0x1ff,(vpn>>8) & 0x1ff,vpn & 0x1ff};
    uint64_t *new_pt=NULL, new_pt_frame_num;
    int i;
    // First map some value that can be traversed.
    tester_page_table_update(pt, vpn, ppn);

    new_pt = phys_to_virt(pt<<12); // #frame -> PTE fromat then take it's address
    if(new_pt == NULL) {
            return EXIT_FAILED;
        }
    uint64_t vpn_slice=0;
    for (i=0; i<5; i++){
        vpn_slice = vpn_slicing[i];
        new_pt[vpn_slice] =  new_pt[vpn_slice] & 0xe ; // only resets the first LSbit.
        if(page_table_query(pt, vpn) != NO_MAPPING) { // check that it fails.
            return EXIT_FAILED;
        }
        new_pt[vpn_slice] =  new_pt[vpn_slice] | 0x1 ; // sets first bit to 1 again.

        if(i==4){
            break;
        }
        new_pt_frame_num = new_pt[vpn_slice] >> 12; // need to pass to phys_to_virt() without any offset.
        new_pt_frame_num = new_pt_frame_num << 12;
        new_pt = phys_to_virt(new_pt_frame_num);
        if(new_pt == NULL) {
            return EXIT_FAILED;
        }
    }
    return EXIT_SUCCESS;
}





int POINTS_DEDUCTION_PER_TEST = 5;
int main(int argc, char **argv)
{
    uint64_t pt = alloc_page_frame(); // the physical page number of this frame
    int student_grade = 100;

    if(test_sanity_check(pt, 0xcafe, 0xf00d) == EXIT_FAILED) {
        printf("basic functionality fails. \n");
        return 60;
    }
    if(test_override_mapping(pt, 0xbafb, 0xaa) == EXIT_FAILED) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }
    if(test_override_prefix_similar_vpn(pt) == EXIT_FAILED) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }
    if(test_mark_leaf_invalid(pt, 0x1fa1, 0xabc) == EXIT_FAILED) {
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    if(test_root_node_not_zero(pt, 0x29a, 0xafab) == EXIT_FAILED) {
        printf("test_root_node_not_zero failed. \n");
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    // Tests for page_table_query()
    if(test_unmapped_from_each_level(pt, 0xb5522, 0xa2222) == EXIT_FAILED) {
        printf("test_unmapped_from_each_level failed. \n");
        student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    // Test that
    if(page_table_query(pt, 0x10000f) != NO_MAPPING) {
       printf("test_big_physical_number. \n");
       student_grade -= POINTS_DEDUCTION_PER_TEST;
    }

    printf("%d\n", student_grade);

	return EXIT_SUCCESS;
}

