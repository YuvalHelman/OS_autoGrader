#include "os.h"


#define LEVEL_NUM 5

/*
 * level from 0 -> (LEVEL_NUM - 1) 
*/
int get_vpn_current_index(uint64_t vpn, int level){
    uint64_t vpn_no_lower_levels = vpn >> (36 - 9*level);
    int current_index = vpn_no_lower_levels & 0x1FF;
    return current_index;
}

/*
* get a legal physical address, that was allocated already, and return the va of the node that the pte points to
*/
uint64_t* pte_to_va(uint64_t pte){
    return (uint64_t*)(phys_to_virt(pte & 0xFFFFFFFFFFFFF000));
}

/*
* create the new pte to put in the dest place in the page table
*/
uint64_t create_new_pte(uint64_t old_ppn,uint64_t new_ppn){
    if(new_ppn == NO_MAPPING){
        return (old_ppn & 0xFFFFFFFFFFFFFFFE);
    }
    else{
        return (new_ppn << 12 | 0x1); // offset = 0, and valid bit = 1
    }
}


/*
* turn the pte that was read from query to ppn to return
*/
uint64_t pte_to_ppn(uint64_t pte){
    if(pte & 0x1){
        return pte >> 12;
    }
    else{
        return NO_MAPPING;
    }
}

/*
* check if the pte is valid by checking the valid bit
*/
int is_pte_valid(uint64_t pte){
    return pte & 0x1;
}

void page_table_update(uint64_t pt, uint64_t vpn, uint64_t ppn){
    uint64_t *node = phys_to_virt(pt << 12);
    int current_index = 0;
    if (node[current_index] == 0){
        node[current_index] = (alloc_page_frame() << 12) + 0x1;
    }
    for(int i = 0; i < LEVEL_NUM; i++){
        current_index = get_vpn_current_index(vpn,i);
        if (node[current_index] == 0){
            node[current_index] = (alloc_page_frame() << 12) + 0x1;
        }
        if(i < LEVEL_NUM - 1){
            node = pte_to_va(node[current_index]);    
        }
    }

    node[current_index] = create_new_pte(node[current_index],ppn);
    
}

uint64_t page_table_query(uint64_t pt, uint64_t vpn) {
    uint64_t *node = phys_to_virt(pt << 12);
    int current_index = 0;
    if (!is_pte_valid(node[current_index])){
        return NO_MAPPING;
    }
    for(int i = 0; i < LEVEL_NUM; i++){
        current_index = get_vpn_current_index(vpn,i);
        if (!is_pte_valid(node[current_index])){
            return NO_MAPPING;
        }
        if (i < LEVEL_NUM - 1){
            node = pte_to_va(node[current_index]);
        }    
    }
    return pte_to_ppn(node[current_index]);
}