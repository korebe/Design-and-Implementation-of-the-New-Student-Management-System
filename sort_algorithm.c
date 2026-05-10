#include <stdlib.h>
#include <string.h>

// 学生结构体定义（与 Python 中一致）
typedef struct {
    int id;
    char student_id[20];
    char name[50];
    char gender[10];
    int age;
    char major[100];
    char phone[20];
    char email[120];
} Student;

// 快速排序比较函数（按年龄升序）
int compare_age_asc(const void *a, const void *b) {
    return ((Student*)a)->age - ((Student*)b)->age;
}

// 快速排序比较函数（按年龄降序）
int compare_age_desc(const void *a, const void *b) {
    return ((Student*)b)->age - ((Student*)a)->age;
}

// 快速排序比较函数（按学号升序）
int compare_id_asc(const void *a, const void *b) {
    return strcmp(((Student*)a)->student_id, ((Student*)b)->student_id);
}

// 对外接口：对学生数组进行排序
void sort_students(Student *students, int count, int sort_mode) {
    switch(sort_mode) {
        case 0: // 按年龄升序
            qsort(students, count, sizeof(Student), compare_age_asc);
            break;
        case 1: // 按年龄降序
            qsort(students, count, sizeof(Student), compare_age_desc);
            break;
        case 2: // 按学号升序
            qsort(students, count, sizeof(Student), compare_id_asc);
            break;
        default:
            break;
    }
}