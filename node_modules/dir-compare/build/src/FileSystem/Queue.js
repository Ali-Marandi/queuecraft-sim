"use strict";
/*

Queue.js

A function to represent a queue

Created by Kate Morley - http://code.iamkate.com/ - and released under the terms
of the CC0 1.0 Universal legal code:

http://creativecommons.org/publicdomain/zero/1.0/legalcode

*/
Object.defineProperty(exports, "__esModule", { value: true });
exports.Queue = void 0;
const MAX_UNUSED_ARRAY_SIZE = 10000;
/* Creates a new queue. A queue is a first-in-first-out (FIFO) data structure -
 * items are added to the end of the queue and removed from the front.
 */
class Queue {
    constructor() {
        // Initialize the queue and offset
        this.queue = [];
        this.offset = 0;
    }
    // Returns the length of the queue.
    getLength() {
        return this.queue.length - this.offset;
    }
    /* Enqueues the specified item. The parameter is:
     *
     * item - the item to enqueue
     */
    enqueue(item) {
        this.queue.push(item);
    }
    /* Dequeues an item and returns it. If the queue is empty, the value
     * 'undefined' is returned.
     */
    dequeue() {
        // if the queue is empty, return immediately
        if (this.queue.length === 0) {
            return undefined;
        }
        // store the item at the front of the queue
        const item = this.queue[this.offset];
        // increment the offset and remove the free space if necessary
        if (++this.offset > MAX_UNUSED_ARRAY_SIZE) {
            this.queue = this.queue.slice(this.offset);
            this.offset = 0;
        }
        // return the dequeued item
        return item;
    }
}
exports.Queue = Queue;
//# sourceMappingURL=Queue.js.map