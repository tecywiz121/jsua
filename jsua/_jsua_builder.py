from cffi import FFI
ffibuilder = FFI()

jsua_header = r'''
#include <jsua/blob.h>
#include <jsua/parser.h>
#include <jsua/error.h>
#include <stdlib.h>

uint8_t* allocate_u8(size_t nmemb) {
    return (uint8_t*)malloc(sizeof(uint8_t) * nmemb);
}

void unallocate_u8(uint8_t* p) {
    free(p);
}
'''

ffibuilder.set_source('jsua._jsua', jsua_header, libraries=['jsua'])

ffibuilder.cdef(r'''
uint8_t* allocate_u8(size_t nmemb);
void unallocate_u8(uint8_t* p);

extern "Python" void pool_give_back(const void*);

typedef void (jsua_free_func)(const void*);
typedef struct jsua_blob jsua_blob;

jsua_blob* jsua_blob_new(void);

void jsua_blob_free(jsua_blob* blob);

void jsua_blob_init_take(jsua_blob* blob,
                         const uint8_t* data,
                         size_t sz,
                         jsua_free_func* dtor);

void jsua_blob_init_empty(jsua_blob* blob);

bool jsua_blob_init_copy(jsua_blob* blob,
                         const uint8_t* data,
                         size_t sz);

void jsua_blob_fini(jsua_blob* blob);

enum jsua_error_type {
    JSUA_ERR_NONE,
    JSUA_ERR_UNTERMINATED_STRING,
    JSUA_ERR_UNTERMINATED_NUMBER,
    JSUA_ERR_UNTERMINATED_LITERAL,
    JSUA_ERR_UNEXPECTED_CHAR,
};
typedef enum jsua_error_type jsua_error_type;

typedef int jsua_error_off;

struct jsua_error {
    jsua_error_type type;
    size_t sample_size;
    jsua_error_off error_offset;
    uint8_t sample[32];
};
typedef struct jsua_error jsua_error;

enum jsua_event_type {
    JSUA_EVT_OBJ_START,
    JSUA_EVT_OBJ_END,
    JSUA_EVT_ARR_START,
    JSUA_EVT_ARR_END,
    JSUA_EVT_VAL_STR,
    JSUA_EVT_VAL_NUM,
    JSUA_EVT_VAL_BOOL,
    JSUA_EVT_VAL_NULL,

    JSUA_EVT_COLON,
    JSUA_EVT_COMMA,
};
typedef enum jsua_event_type jsua_event_type;

struct jsua_event {
    /**
     * The type of the triggered event.
     */
    jsua_event_type type;

    /**
     * Whether this is is the last chuck of the event. Will only be false if the
     * data crosses a blob boundary and this isn't the last blob.
     */
    bool completed;

    /**
     * Number of uint8_t in the array pointed to by data.
     */
    size_t size;

    /**
     * The data associated with the event, or NULL if there isn't any.
     */
    const uint8_t* data;
};
typedef struct jsua_event jsua_event;

typedef void (jsua_parser_evt_func)(jsua_event* event, void* user_data);

extern "Python" void on_parser_event(jsua_event*, void*);

typedef struct jsua_parser jsua_parser;

jsua_parser* jsua_parser_new(void);
void jsua_parser_free(jsua_parser* parser);

bool jsua_parser_init(jsua_parser* parser,
                               jsua_parser_evt_func* cb,
                               void* user_data);

void jsua_parser_fini(jsua_parser* parser);

bool jsua_parser_feed(jsua_parser* parser,
                               jsua_blob* blob);

const jsua_error* jsua_parser_error(jsua_parser* parser);
const char* jsua_error_to_string(const jsua_error* err);
''')

if __name__ == '__main__':
    ffibuilder.compile()
