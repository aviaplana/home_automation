#ifndef NODELIST_H
#define NODELIST_H

#include <Arduino.h>

typedef struct node_t {
    byte id;
    byte pipe;
    struct node_t* next;
};

class NodeList {
  public:
    NodeList();
    void deleteNode(byte);
    void deleteAll();
    bool addNode(byte, byte);
    node_t* searchNode(byte);
    byte getPipe(byte);
    bool isEmpty() { return (node_list == NULL) ? true : false; };

  private:
    node_t* node_list;
    
};

#endif
